from core.langgraph_.schema import AgentState
import os

def contextual_prompt_generator(state: AgentState):
    prompts = state['prompter_output'].prompts
    contextual_prompts = []

    os.makedirs(f"Storage/{state['concept']}",exist_ok=True)
    
    for i, p in enumerate(prompts):
        if p == "No figure":
            continue

        contextual_prompts.append({
            "figure_id": f"fig_{i}",
            "prompt": (
                p+ "\nfigure name: "+ f"fig_{i}"+ "\n folder name:"+ state["concept"].replace(" ","_") if i == 0 else
                "<Older Prompts/Explanation Steps>\n"
                + "\n".join(prompts[:i])
                + "\n<Current Explanation Step/prompt>\n"
                + p
                + "\nfigure name:"+ f"fig_{i}"
                + "\n folder name:"+ state["concept"].replace(" ","_")
            )
        })

    return {"contextual_prompts": contextual_prompts}