import os
from PIL import Image
from pathlib import Path
import torch
from transformers import TableTransformerForObjectDetection, DetrFeatureExtractor
import matplotlib.pyplot as plt
import fitz
import shutil
from scripts.constants import Constants


def pdf_to_images(pdf_path: str, output_dir: str, zoom: float = 3.0):
        pdf_name = Path(pdf_path).stem
        pdf_document = fitz.open(pdf_path)
        os.makedirs(output_dir, exist_ok=True)

        mat = fitz.Matrix(zoom, zoom)
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap(matrix=mat)
            img_path = os.path.join(output_dir, f"{pdf_name}_{page_num + 1}.png")
            pix.save(img_path)


class TableDetection:

    def __init__(self, model_name="microsoft/table-transformer-detection"):
        self.model = TableTransformerForObjectDetection.from_pretrained(model_name)
        self.feature_extractor = DetrFeatureExtractor()
        self.colors = [[0.000, 0.447, 0.741], [0.850, 0.325, 0.098], [0.929, 0.694, 0.125],
                       [0.494, 0.184, 0.556], [0.466, 0.674, 0.188], [0.301, 0.745, 0.933]] * 100


    def find_tables(self, image: Image.Image, threshold: float, save_path: str):
        width, height = image.size

        encoding = self.feature_extractor(image, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**encoding)

        results = self.feature_extractor.post_process_object_detection(
            outputs,
            threshold=threshold,
            target_sizes=[(height, width)]
        )[0]

        self.plot_results(
            image, 
            results['scores'], 
            results['labels'], 
            results['boxes'], 
            save_path
        )


    def plot_results(self, pil_img: Image.Image, scores, labels, boxes, save_path: str):
        plt.figure(figsize=(16, 10))
        plt.imshow(pil_img)
        ax = plt.gca()

        for score, label, (xmin, ymin, xmax, ymax), color in zip(scores.tolist(), labels.tolist(), boxes.tolist(), self.colors):
            ax.add_patch(plt.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin,
                                       fill=False, color=color, linewidth=3))
            text = f'{self.model.config.id2label[label]}: {score:0.2f}'
            ax.text(xmin, ymin, text, fontsize=15, bbox=dict(facecolor='yellow', alpha=0.5))

        plt.axis('off')
        plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
        plt.close()


    def process_pdfs(self, images_path: str, output_path: str):
        os.makedirs(output_path, exist_ok=True)
        for pdf_file in os.listdir(images_path):
            if pdf_file.endswith('.pdf'):
                pdf_to_images(os.path.join(images_path, pdf_file), output_path)


    def analyze_images(self, images_path: str, threshold: float, result_path: str):
        os.makedirs(result_path, exist_ok=True)

        for image_name in os.listdir(images_path):
            image_path = os.path.join(images_path, image_name)
            output_image_path = os.path.join(result_path, image_name)

            if not os.path.exists(output_image_path):
                self.find_tables(Image.open(image_path), threshold, output_image_path)


    def detect_tables(self, articles_path: str, threshold: float, results_path: str):
        images_dir = Constants.Directories.TEMP
        
        self.process_pdfs(articles_path, images_dir)
        self.analyze_images(images_dir, threshold, results_path)

        shutil.rmtree(images_dir)
