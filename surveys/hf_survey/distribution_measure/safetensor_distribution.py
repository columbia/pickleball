import os
import json
import huggingface_hub
from huggingface_hub import hf_hub_download, HfApi

# Make a bar chart for cnt
import matplotlib.pyplot as plt
import numpy as np

from tqdm import tqdm

api = HfApi()

hf_domains  = {
            'Multimodal': ['feature-extraction', 'text-to-image', 'image-to-text', 'text-to-video', 'visual-question-answering', 'graph-machine-learning'],
            'Computer Vision': ['depth-estimation', 'image-classification', 'object-detection', 'image-segmentation', 'image-to-image', 'unconditional-image-generation', 'video-classification', 'zero-shot-image-classification'],
            'NLP': ['text-classification', 'token-classification', 'table-question-answering', 'question-answering', 'zero-shot-classification', 'translation', 'summarization', 'conversational', 'text-generation', 'text2text-generation', 'fill-mask', 'sentence-similarity', 'table-to-text', 'multiple-choice', 'text-retrieval'],
            'Audio': ['text-to-speech', 'text-to-audio', 'automatic-speech-recognition', 'audio-to-audio', 'audio-classification', 'voice-activity-detection'],
            'Other': ['reinforcement-learning', 'robotics', 'tabular-classification', 'tabular-regression', 'tabular-to-text', 'time-series-forecasting']
        }


FILE_EXTENSIONS = [".bin", ".safetensors", ".pt", ".pth", ".pkl"]

FRAMEWORK_LIST = ["pytorch", "safetensors"]


def get_models():
    models_list = {}
    # init cnt variables for each framework

    distribution_pt_st = {'pt': 0, 'st': 0, 'both': 0, 'none': 0}
    cnt_fram = {}
    for domain in hf_domains:
        cnt_fram[domain] = {}
        for framework in FRAMEWORK_LIST:
            cnt_fram[domain][framework] = 0
        
    cnt_ext = {}
    for domain in hf_domains:
        cnt_ext[domain] = {}
        for ext in FILE_EXTENSIONS:
            cnt_ext[domain][ext] = 0


    # count the number of models for each domain and task
    num_models = {}
    for domain in hf_domains:
        num_models[domain] = {}
        models_list[domain] = {}
        for task in hf_domains[domain]:
            models_list[domain][task] = []
            num_models[domain][task] = 0
            # models = list(api.list_models(filter=task, sort="downloads", direction=-1, limit=100))
            models = list(api.list_models(filter=task, sort="last_modified", direction=-1, limit=100))
            
            num_models[domain][task] += len(models)
            for model in tqdm(models):
                models_list[domain][task].append(model.id)
                for framework in FRAMEWORK_LIST:
                    if framework in model.tags:
                        cnt_fram[domain][framework] += 1
                if "pytorch" in model.tags and "safetensors" in model.tags:
                    distribution_pt_st['both'] += 1
                elif "pytorch" in model.tags:
                    distribution_pt_st['pt'] += 1
                elif "safetensors" in model.tags:
                    distribution_pt_st['st'] += 1
                else:
                    distribution_pt_st['none'] += 1
                
                # check files
                try:
                    files = list(api.list_repo_tree(model.id))
                except:
                    continue
                
                for file in files:
                    for ext in FILE_EXTENSIONS:
                        if ext in file.path:
                            cnt_ext[domain][ext] += 1
                            
                    
    with open('models_list.json', 'w') as f:
        json.dump(models_list, f)

    # Save the results
    with open('cnt_fram.json', 'w') as f:
        json.dump(cnt_fram, f)

    with open('cnt_ext.json', 'w') as f:
        json.dump(cnt_ext, f)

    with open('distribution_pt_st.json', 'w') as f:
        json.dump(distribution_pt_st, f)
    return 


def plot_cnt(cnt_fram, cnt_ext):
    # Plot the percentage distribution of frameworks
    fig, ax = plt.subplots(figsize=(12, 8))
    domains = list(cnt_fram.keys())
    frameworks = FRAMEWORK_LIST

    # Calculate total counts per domain for sorting
    total_counts_per_domain = {domain: sum(cnt_fram[domain].values()) for domain in domains}
    sorted_domains = sorted(domains, key=total_counts_per_domain.get, reverse=True)

    ind = np.arange(len(sorted_domains))
    width = 0.35

    for i, framework in enumerate(frameworks):
        percentages = [cnt_fram[domain].get(framework, 0) / total_counts_per_domain[domain] * 100 if total_counts_per_domain[domain] > 0 else 0 for domain in sorted_domains]
        ax.bar(ind + i*width, percentages, width, label=framework)

    ax.set_ylabel('Percentage (%)', fontsize=16)
    ax.set_title('Percentage by framework and domain', fontsize=22)
    ax.set_xticks(ind + width / 2)
    ax.set_xticklabels(sorted_domains, rotation=45, fontsize=16)
    ax.legend(loc='best')
    ax.tick_params(axis='y', labelsize=12)

    plt.tight_layout()
    plt.savefig('percentage_framework_distribution.png')

    # Plot the percentage distribution of file extensions
    fig, ax = plt.subplots(figsize=(12, 8))
    width = 0.15  # Width of the bars
    ind = np.arange(len(domains))  # The x locations for the groups

    # Plot bars for each file extension in the reversed fixed order
    for i, ext in enumerate(FILE_EXTENSIONS):
        percentages_ext = [cnt_ext[domain].get(ext, 0) / sum(cnt_ext[domain].values()) * 100 if sum(cnt_ext[domain].values()) > 0 else 0 for domain in domains]
        bars = ax.bar(ind + i*width, percentages_ext, width, label=ext)

        # Annotate bars with the percentage value
        # for bar in bars:
        #     height = bar.get_height()
        #     ax.annotate(f'{height:.1f}%',
        #                 xy=(bar.get_x() + bar.get_width() / 2, height),
        #                 xytext=(0, 3),  # 3 points vertical offset
        #                 textcoords="offset points",
        #                 ha='center', va='bottom', fontsize=12)

    ax.set_ylabel('Percentage (%)', fontsize=16)
    ax.set_title('Percentage of File Extensions by Domain', fontsize=22)
    ax.set_xticks(ind + width * (len(FILE_EXTENSIONS) - 1) / 2)
    ax.set_xticklabels(domains, fontsize=20, rotation=45)
    ax.set_yticklabels([f'{i}%' for i in range(0, 101, 10)], fontsize=16)
    ax.legend(title="File Extension", bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.savefig('percentage_file_extension_distribution.png')
    return


def plot_distribution_pt_st():
    with open ('distribution_pt_st.json', 'r') as f:
        distribution_pt_st = json.load(f)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    labels = ['PyTorch', 'SafeTensors', 'Both', 'None']
    # labels = list(distribution_pt_st.keys())
    sizes = list(distribution_pt_st.values())
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 20})
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title('Distribution of models (Pytorch and Safetensors)', fontsize=22)
    plt.savefig('distribution_pt_st.png')
    return


if __name__ == "__main__":
    if not os.path.exists('cnt_fram.json') and not os.path.exists('cnt_ext.json'):
        get_models()
    
    with open ('cnt_fram.json', 'r') as f:
        cnt_fram = json.load(f)
    
    with open ('cnt_ext.json', 'r') as f:
        cnt_ext = json.load(f)

    plot_cnt(cnt_fram, cnt_ext)

    plot_distribution_pt_st()