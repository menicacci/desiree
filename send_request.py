import os
import json
import time
import tiktoken
from openai import AzureOpenAI


def extract_infos(json_file_path) -> dict:
    with open(json_file_path, 'r') as file:
        return json.load(file)


def init_client(infos: dict):
    client = AzureOpenAI(
        azure_endpoint=infos['azure_endpoint'],
        api_key=infos['api_key'],
        api_version=infos['api_version']
    )

    return client


def num_tokens_from_string(string: str) -> int:
    encoding = tiktoken.encoding_for_model("gpt-4")
    num_tokens = len(encoding.encode(string))

    return num_tokens


def message(role, content) -> dict:
    return {"role": role, "content": content}


def read_file(absolute_path):
    with open(absolute_path) as file:
        return file.read()


def build_messages(file_name: str, output_prompts_folder: str, instructions: str, request: str):
    messages_dict = [
        message("system", instructions),
        message("user", request)
    ]

    # save prompt for replication purposes
    file_name_txt = file_name + '.txt'
    with open(os.path.join(output_prompts_folder, file_name_txt), "w") as text_file:
        text_file.write(json.dumps(messages_dict))
    print(f"\t Saved prompt at: {os.path.join(output_prompts_folder, file_name_txt)}")

    # number of input tokens
    input_tokens = num_tokens_from_string(instructions + request)

    return messages_dict, input_tokens


def send_request(client, prompt: dict, max_tokens=16000):
    start_time = time.time()

    with client.chat.completions.with_streaming_response.create(
            model="gpt-4-32k",  # model = "deployment_name".
            max_tokens=6000,
            temperature=0,
            stream=True,
            messages=prompt,
    ) as response:

        answer = ''
        current_answer = ''
        output_tokens = 0
        stream = ''

        for line in response.iter_lines():

            stream += line + '\n'

            if len(line) > 0:
                output_tokens += 1
                line = line.replace('data: ', '')
                if line == '[DONE]':
                    break
                json_line = json.loads(line)
                if len(json_line['choices']) > 0 and json_line['choices'][0] != None and json_line['choices'][0][
                    'delta'] != None and len(json_line['choices'][0]['delta']) > 0 and json_line['choices'][0]['delta'][
                    'content'] != None:
                    current_token = json_line['choices'][0]['delta']['content']
                    # answer += json_line['choices'][0]['delta']['content']
                    answer += current_token
                    current_answer += current_token
                    if '\n' in current_token:
                        print(current_answer)
                        current_answer = ''

    request_time = time.time() - start_time
    return answer, output_tokens, request_time, stream


def save_answer(answer, output_answers_folder, file_name):
    file_name_txt = file_name + '.txt'
    with open(os.path.join(output_answers_folder, file_name_txt), "w") as text_file:
        text_file.write(answer)
    print(f"\t Saved answer at: {os.path.join(output_answers_folder, file_name_txt)}")

    return


def run(connection_data: dict, output_prompts_folder: str, output_answers_folder: str, instructions: str, request: str,
        request_id: str):
    client = init_client(connection_data)

    prompt, input_tokens = build_messages(request_id, output_prompts_folder, instructions, request)
    print(f"Sending request [{request_id}]")
    answer, output_tokens, request_time, stream = send_request(client, prompt)

    save_answer(answer, output_answers_folder, request_id)


prompts_folder = 'requests/prompts'
answers_folder = 'requests/answers'
connection_infos = extract_infos('private.json')

instr = '''
Act as a computer scientist researcher. You have to extract all the possible structured information from a semi-structured table given in HTML. The structured information to extract are called conditional claims and they have the following structure: <{list of specifications}, m, o>. "m" is the measure or metric (statistical, physical, or any other kind of measure, including interval valued) used in the table to express the scientific results of the experiment while outcome is the associated result. The list of specifications is a list of couples that follow this structure: <name, value>, where name is the type of specification and value is the value of the specification. Value must always be present in the table, while you can infer the name if it is implied in the table. A specification is everything that has been reported in the table to characterize, define or circumscribe the outcome (i.e., the conditions under which the outcome is valid). You have to extract one claim for each outcome.

For example, extract JUST THE FIRST TWO CLAIMS (and nothing else) from this table:

<figure><figcaption><span>TABLE I: </span>Average execution delay for various resolution layers compared to the average delay of the one-shot computation.</figcaption><table><thead><tr><th>Average delay</th><th><math><semantics><mrow><mi>l</mi><mo>=</mo><mn>1</mn></mrow><annotation-xml><apply><eq></eq><ci></ci><cn>1</cn></apply></annotation-xml><annotation>l=1</annotation></semantics></math></th><th><math><semantics><mrow><mi>l</mi><mo>=</mo><mn>2</mn></mrow><annotation-xml><apply><eq></eq><ci></ci><cn>2</cn></apply></annotation-xml><annotation>l=2</annotation></semantics></math></th><th><math><semantics><mrow><mi>l</mi><mo>=</mo><mn>3</mn></mrow><annotation-xml><apply><eq></eq><ci></ci><cn>3</cn></apply></annotation-xml><annotation>l=3</annotation></semantics></math></th><th><math><semantics><mrow><mi>l</mi><mo>=</mo><mn>4</mn></mrow><annotation-xml><apply><eq></eq><ci></ci><cn>4</cn></apply></annotation-xml><annotation>l=4</annotation></semantics></math></th><th>One-shot</th></tr></thead><tbody><tr><th>Empirical</th><td><math><semantics><mn>11.33</mn><annotation-xml><cn>11.33</cn></annotation-xml><annotation>11.33</annotation></semantics></math></td><td><math><semantics><mn>18.12</mn><annotation-xml><cn>18.12</cn></annotation-xml><annotation>18.12</annotation></semantics></math></td><td><math><semantics><mn>24.92</mn><annotation-xml><cn>24.92</cn></annotation-xml><annotation>24.92</annotation></semantics></math></td><td><math><semantics><mn>31.71</mn><annotation-xml><cn>31.71</cn></annotation-xml><annotation>31.71</annotation></semantics></math></td><td><math><semantics><mn>32.43</mn><annotation-xml><cn>32.43</cn></annotation-xml><annotation>32.43</annotation></semantics></math></td></tr></tbody></table></figure>

<{<Average delay, Empirical>, <Layer (l), 1>}, Execution delay, 11.33>
<{<Average delay, Empirical>, <Layer (l), 1>}, Execution delay, 18.12>


Respond just with the conditional claims. Don't enumerate them in any way. You can not answer with something like "and so on".
'''

req = '''
Extract ALL the conditional claims (and nothing else, but write down all the conditional claims with the respective specifications, do not be lazy by writing just some of the claims) from this table:

\begin{table*}[ht!]\centering
\renewcommand{\tabcolsep}{2.8pt}
{\small
\caption{{
Characteristics of the new datasets generated by
DeepBlocker~\cite{DBLP:journals/pvldb/Thirumuruganathan21}. The
blocking performance is reported with recall ($PC$),
precision ($PQ$), the total number of candidates ($|C|$) and the
number of matching candidates ($|P|$). DeepBlocker applies
Autoenconder to the selected attribute(s) ($attr.$) using
stemming and stop-word removal 
or not ($cl.$), and $K$ candidates per query record of the indexed
dataset ($ind.$).}}
	\begin{tabular}{ | l | c |  c | r | r | c || c | c | r | r || c | c | r | c || r | r |  r | r | r | r | r |}
		\cline{1-21}
		 \multicolumn{1}{|c|}{} & 
		 \multirow{2}{*}{$D_1$} & 
		 \multirow{2}{*}{$D_2$} & 
         \multicolumn{1}{c|}{\multirow{2}{*}{$|D_1|$}} & 
         \multicolumn{1}{c|}{\multirow{2}{*}{$|D_2|$}} & 
         \multirow{2}{*}{$|A|$} &
         \multicolumn{4}{c||}{Blocking performance} & 
         \multicolumn{4}{c||}{DeepBlocker config.} & 
         \multicolumn{1}{c|}{\multirow{2}{*}{$|I_{tr}|$}} & 
         \multicolumn{1}{c|}{\multirow{2}{*}{$|I_{te}|$}} & 
         \multicolumn{1}{c|}{\multirow{2}{*}{$|P_{tr}|$}} &
         \multicolumn{1}{c|}{\multirow{2}{*}{$|P_{te}|$}} & 
         \multicolumn{1}{c|}{\multirow{2}{*}{$|N_{tr}|$}} & 
         \multicolumn{1}{c|}{\multirow{2}{*}{$|N_{te}|$}} &
         \multicolumn{1}{c|}{\multirow{2}{*}{IR}} \\
         \multicolumn{1}{|c|}{} & & & & & & 
         \multicolumn{1}{c|}{$PC$} & 
         \multicolumn{1}{c|}{$PQ$} & 
         \multicolumn{1}{c|}{$|C|$} &
         \multicolumn{1}{c||}{$|P|$} &
         \multicolumn{1}{c|}{$attr.$} & 
         \multicolumn{1}{c|}{$cl.$} & 
         \multicolumn{1}{c|}{$K$} & 
         \multicolumn{1}{c||}{$ind.$} & & & & & & & \\
        \hline
        \hline
        $D_{n1}$ & Abt & Buy & 1,076 & 1,076 & 3 & 0.899 & 0.029 & 33,356 & 967 & name & $\times$ & 31 & $D_2$ & 20,014 & 6,671 & 580 & 193 & 19,433 & 6,478 & 2.9\%\\
        $D_{n2}$ & Amazon & GP & 1,354 & 3,039 & 4 & 0.910 & 0.074 & 13,540 & 1,005	 & title & $\times$ & 10 & $D_1$ & 8,124 & 2,708 & 603 & 201 & 7,521 & 2,507 & 7.4\%\\
        $D_{n3}$ & DBLP & ACM & 2,616 & 2,294 & 4 & 0.983 & 0.953 & 2,294 & 2,186 & all & \checkmark & 1	 & $D_2$ & 1,376 & 459 & 1,312 & 437 & 65 & 22 & 95.3\%\\
        $D_{n4}$ & IMDB & TMDB & 5,118 & 6,056 & 5 & 0.898 & 0.011 & 158,658 & 1,768 & all & \checkmark	 & 31 & $D_1$ & 95,195 & 31,732 & 1,061 & 354 & 94,134 & 31,378 & 1.1\%\\
        $D_{n5}$ & IMDB & TVDB & 5,118 & 7,810 & 4 & 0.891 & 0.003 & 322,434 & 955 & all & $\times$	 & 63 & $D_1$ & 193,460 & 64,487 & 573 & 191 & 192,887 & 64,296 & 0.3\%\\
        $D_{n6}$ & TMDB & TVDB & 6,056 & 7,810 & 6 & 0.927 & 0.130 & 7,810 & 1,015 & all & \checkmark & 1 & $D_2$ & 4,686 & 1,562 & 609 & 203 & 4,077 & 1,359 & 13.0\%\\
        $D_{n7}$ & Walmart & Amazon & 2,554 & 22,074 & 6 & 0.894 & 0.018 & 43,418 & 763 & all	 & \checkmark & 17 & $D_1$ & 26,051 & 8,684 & 458 & 153 & 25,593 & 8,531 & 1.8\%\\
        $D_{n8}$ & DBLP & GS & 2,516 & 61,353 & 4 & 0.906 & 0.166 & 12,580 & 2,091 & all & \checkmark & 5 & $D_1$ & 7,548 & 2,516 & 1,255 & 418 & 6,293 & 2,098 & 16.6\%\\
	\hline
	\end{tabular}
	\label{tb:newDatasets}
}
\end{table*}
'''

req_id = '0013'

run(connection_infos, prompts_folder, answers_folder, instr, req, req_id)
