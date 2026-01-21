from core.langgraph_.schema import AgentState
import os


def contextual_prompt_generator(state: AgentState):
    """
    Generates contexual prompts
    
    :param state: Current state of the agent
    :type state: AgentState
    """

    prompts = state["prompter_output"].prompts
    contextual_prompts = []

    # create the directory for the concept.
    os.makedirs(f"Storage/{state['concept']}", exist_ok=True)

    # generate contexual prompt for each prompt
    for i, p in enumerate(prompts):
        # if a certain explanation step doesn't require a figure
        if p == "No figure": 
            continue
        
        contextual_prompts.append(
            {
                "figure_id": f"fig_{i}",
                "prompt": (
                    p
                    + "\nfigure name: "
                    + f"fig_{i}"
                    + "\n folder name:"
                    + state["concept"].replace(" ", "_")
                    if i == 0 # for the first prompt we don't need any context for previous prompts.
                    else "<Older Prompts/Explanation Steps>\n" 
                    + "\n".join(prompts[:i])
                    + "\n<Current Explanation Step/prompt>\n"
                    + p
                    + "\nfigure name:"
                    + f"fig_{i}"
                    + "\n folder name:"
                    + state["concept"].replace(" ", "_")
                ),
            }
        )

    return {"contextual_prompts": contextual_prompts}
