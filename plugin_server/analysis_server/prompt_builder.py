from textwrap import dedent

ALLOWED_RISK_TYPES = {
    "root-privilege-user",
    "use-sudo-run",
    "yum-install-without-version",
    "apt-install-without-version",
    "pip-install-without-version",
    "use-add-instead-of-copy",
    "use-deprecated-maintainer",
    "miss-apt-no-install-recommends",
    "miss-specific-tags",
    "use-cd-change-dir",
}

def build_prompt(dockerfile: str, predicted_risks: list[dict], context_lookup: dict[str, list[str]]) -> str:
    # 仅保留 10 类允许的风险
    filtered = [r for r in predicted_risks if r.get("risk_type") in ALLOWED_RISK_TYPES]

    # 供模型参考的“风险详情”（不要求回显）
    analysis_blocks = []
    for idx, r in enumerate(filtered, 1):
        ctx_docs = context_lookup.get(r["risk_type"], [])
        context = "\n".join(ctx_docs) if ctx_docs else "There is not any recommended remediation measures."
        analysis_blocks.append(dedent(f"""
        - Risk{idx}: {r["risk_type"]}
        - description:
            {context}
        """).strip())
    analysis = "\n".join(analysis_blocks)

    # 供模型参考的“检测到的风险列表”（不要求回显）
    risk_lines = []
    for r in filtered:
        position = f"character {r['start']}-{r['end']}" if r.get("start", -1) != -1 and r.get("end", -1) != -1 else "without position"
        snippet = (r.get("snippet") or "").replace("\n", "\\n")
        risk_lines.append(f"- Risk type: {r['risk_type']}, Snippet: {snippet}, Position: {position}")
    risks = "\n".join(risk_lines)

    # 无风险输入（或经过滤后无）→ 直接返回无风险模板
    if not filtered:
        return dedent("""
        ## Analysis Results

        ### Secure code

        Congratulations! The file you provided has no security risks.

        ### Good development practice

        [secure practice]:[description]

        [secure practice]:[description]

        [secure practice]:[description]
        """).strip()

    # 更强的“格式钉死”：给出可填写模板，要求仅替换占位符
    prompt = dedent(f"""
    You are a senior cloud security engineer specializing in Dockerfile best practices.

    # Task
    Validate the detected risks against the actual Dockerfile, then **fill in the output template below**.
    - You MUST begin your answer with the line: `## Analysis Results`
    - You MUST keep every heading and bullet exactly as shown.
    - Replace ONLY the bracketed placeholders like `[risk name]`, `[number of risk line]`, etc.
    - Do NOT add or remove headings, sections, or code fences.
    - Do NOT output anything outside the chosen template (Case A or Case B).

    # Validation & Relocation Rules (must follow)
    1) Allowed risk types (ignore all others): {", ".join(sorted(ALLOWED_RISK_TYPES))}
    2) Treat snippet/char-range as hints only; derive **true line numbers** from the file.
    3) If the hinted spot is wrong or Not-Present there, you MUST scan the **entire file** for the **same risk type** using these rules:
       - **miss-specific-tags**: `FROM` must have a specific tag (e.g., `FROM ubuntu:20.04`); `latest` is insecure; no tag → risk.
       - **miss-apt-no-install-recommends**: `apt-get install` must include `--no-install-recommends`.
       - **apt/yum/pip-install-without-version**: every installed package must be pinned to exact versions (e.g., `=1.2.3`).
       - **use-sudo-run**: using `sudo` in `RUN` is a risk.
       - **root-privilege-user**: default root or `USER root` is a risk; prefer non-root at the end.
       - **use-add-instead-of-copy**: prefer `COPY` unless `ADD` is necessary (archive/remote/extract).
       - **use-deprecated-maintainer**: `MAINTAINER` is deprecated.
       - **use-cd-change-dir**: avoid `RUN cd ... && ...`; use `WORKDIR`.
    4) If same-type risk exists elsewhere, include it with correct line number(s) and exact line content; if nowhere, SKIP it (do not output that risk).
    5) Line numbers refer to lines of the provided Dockerfile split by newline from the first visible line.
    6) Multi-line risks: list each risky line with its own number & exact text.

    # Fix Rules (must follow)
    - Under `## Completed fixed code`, output the **entire** Dockerfile with fixes in place.
    - Keep unrelated lines identical and order preserved.
    - For every fix, add exactly one comment line immediately above it:
      `#Bugs: [the original risky line as it appears in the file]`
    - Do NOT introduce unrelated changes (e.g., do not change CMD, reorder blocks, or add packages unless required by the fix).

    # Output Template
    Choose **exactly one** case and fill the placeholders. If zero verified risks after validation, use Case A; otherwise strictly fill Case B.
    If any required section in Case B is missing or out of order, REPRINT the full Case B template from the start with all placeholders filled.

    ## Case A — No Verified risks after validation (print exactly this if zero verified risks)

    ## Analysis Results

    ### Secure code

    Congratulations! The file you provided has no security risks.

    ### Good development practice

    [secure practice]:[description]

    [secure practice]:[description]

    [secure practice]:[description]

    ## Case B — At least 1 Verified risk (fill EVERYTHING below; keep headings and bullets exactly)

    ## Analysis Results

        ### Risk1: [risk name]

          - **description** : [rationale of risk]

          - **risk level** : [risk level]
          
          - **risk line** : 
            - **line number** : [number of risk line]
            - **line conten** t: [content of risk line]
          
          - **recommendations** :
            - **fix recommendations** : [fix recommendations]
            - **secure usage** : [explain the secure usage formation]
            - **secure example** : [fixed content of the risk line]
          - **references** :
            - [reference link with more information]


        ### Risk2: ...
        ### Risk3: ...

      ## Completed fixed code

        ```
          [secure dockerfile]
        ```

      ## Advantages analysis

      1.**[Advantages name]** : [advantages description]

      2.**[Advantages name]** : [advantages description]
      
      3.**[Advantages name]** : [advantages description]

    # Inputs (hints; do not echo back)
    Detected risks:
    {risks}

    Related risk details and remediation advice:
    {analysis}

    Original Dockerfile:
    ```
    {dockerfile}
    ```

    # Final rule
    - Output ONLY the chosen template (A or B) with placeholders filled.
    - Begin with `## Analysis Results`. If your output starts with code or with `## Completed fixed code`, discard and reprint Case B from the start.
    """).strip()

    return prompt