import sys
from yachalk import chalk
sys.path.append("..")

import json
import ollama.client as client

##TODO Customize to be domain specific
def extractConcepts(prompt: str, metadata={}, model="yichat:34"):
    SYS_PROMPT = (
    "Your task is to extract key concepts and non-personal entities related to cybersecurity from the given technical analysis of malware files and families. "
    "Focus on the most crucial and discrete concepts, breaking down complex concepts into simpler, more fundamental elements when necessary. "
    "Classify the concepts into one of the following categories specific to malware analysis: "
    "[indicator of compromise (IOC), file hash, threat actor, malware family, vulnerability, tool, technique, network signature, domain, IP address, URL, artifact, campaign, tactic, procedure, infrastructure, software, organization, document, event, misc]\n"
    "Structure your output as a list in JSON format, using the following template:\n"
    "[\n"
    " {\n"
    ' "entity": The specific cybersecurity concept or entity,\n'
    ' "importance": The contextual importance of the entity in the scope of malware analysis on a scale of 1 to 5 (5 being the highest),\n'
    ' "category": The category of the entity as listed above,\n'
    " },\n"
    "{ },\n"
    "]\n"
    "Ensure the extracted information is accurate and relevant to the cybersecurity context, highlighting the connections between malware attributes and their implications for security postures."
    )
    response, _ = client.generate(model_name=model, system=SYS_PROMPT, prompt=prompt)
    try:
        result = json.loads(response)
        result = [dict(item, **metadata) for item in result]
    except:
        print("\n\nERROR ### Here is the buggy response: ", response, "\n\n")
        result = None
    return result

##TODO Customize to be domain specific
def graphPrompt(input: str, metadata={}, model="yichat:34"):
    if model == None:
        model = "mistral-openorca:latest"

    # model_info = client.show(model_name=model)
    # print( chalk.blue(model_info))

    SYS_PROMPT = (
    "As an entity relationship analyzer specializing in cybersecurity, your objective is to parse technical documents on malware analysis and distill key information into a structured network graph. "
    "You will receive excerpts of text (enclosed within triple backticks) containing technical descriptions and analyses of malware threats. Your task is to extract the essential ontology of terms related to malware attributes, indicators of compromise (IOCs), threat actors, and cybersecurity measures mentioned within the text. \n"
    "Thought 1: As you evaluate each sentence, identify the fundamental terms. These may encompass cybersecurity-specific objects, entities, malware families, techniques, vulnerabilities, infrastructures, and other relevant terms. Focus on atomistic and granular details.\n\n"
    "Thought 2: Determine the potential connections between these terms. It's reasonable to infer that terms appearing in close proximity (within the same sentence or paragraph) have a relationship. A term can be connected to multiple other terms, forming a network of relationships.\n\n"
    "Thought 3: Define the relationship for each identified pair of related terms based on their context within the cybersecurity domain. \n\n"
    "Present your findings in a JSON list format. Each entry should detail a pair of related terms along with a description of their relationship. The output should be constructed as follows: \n"
    "[\n"
    " {\n"
    ' "node_1": "Specific cybersecurity term from the ontology",\n'
    ' "node_2": "Another related term from the ontology",\n'
    ' "edge": "The nature of the relationship between node_1 and node_2, articulated in a concise manner"\n'
    " }, {...}\n"
    "]\n"
    "Your analysis should be precise, capturing the complex interplay of terms within the context of malware and cybersecurity."
    )

    USER_PROMPT = f"context: ```{input}``` \n\n output: "
    response, _ = client.generate(model_name=model, system=SYS_PROMPT, prompt=USER_PROMPT)
    try:
        result = json.loads(response)
        result = [dict(item, **metadata) for item in result]
    except:
        print("\n\nERROR ### Here is the buggy response: ", response, "\n\n")
        result = None
    return result
