def build_prompt(purpose, systems):
    prompt = "Analyze the following source-code snippets and relying only on the information from the snippets, tell me the supported operating systems. Ignore any snippets that has no relevant information to operating systems.\n"

    prompt += "------- SYSTEM SNIPPETS -------\n"

    for i, (t, filepath, line, ctx) in enumerate(systems, 1):
        prompt += f"[{i}] FILE: {filepath}:{line}\n"
        prompt += f"CONTEXT: {ctx}\n\n"

    return prompt
