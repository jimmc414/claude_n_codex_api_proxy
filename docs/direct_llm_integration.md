# Direct LLM Integration Without Cloud API Keys

This document explains how the proxy contained in this repository works and
provides a clear specification for adapting an existing program so that it can
reach Claude Code (Claude Max) or Codex (ChatGPT Pro / Code Interpreter) via the
locally installed CLI tools rather than the public cloud APIs. The instructions
are written so another developer or model can follow them to migrate a
codebase.

> **Important reality check**
>
> * Anthropic and OpenAI do not expose a fully supported, keyless programming
>   interface for their web-only subscription tiers. Both vendors rely on local
>   CLI tooling that authenticates an interactive user session. Therefore this
>   document describes how to reuse those vendor-provided CLIs (which store
>   session credentials on disk after a `login` command) and how to route data
>   between your program and the CLI process. There is no way to bypass vendor
>   authentication or licensing requirements.
>
> * The approach below only works for users who already have access to Claude
>   Max (via the `claude` CLI that ships with Claude Code) or ChatGPT Pro / Codex
>   (via the `codex` CLI or `openai` CLI with the "Desktop" beta features). If a
>   user does not have those entitlements the migration cannot succeed.

## 1. How the Existing Proxy Works

The repository ships a universal HTTP proxy and Python router that detect when a
request is using a sentinel API key (all `9`s). When the sentinel key is used,
requests are transparently redirected to the local Claude Code or Codex CLI
instead of the remote REST endpoints. The routing logic lives in
`claude_code_client.py` and `codex_client.py`. These clients:

1. Convert the Anthropic/OpenAI request payload into a single prompt string that
   the CLI can consume via standard input.
2. Spawn the CLI with `subprocess` helpers defined in `utils.py`.
3. Read the CLI's stdout, then convert it back into the JSON structures expected
   by the SDK that initiated the call.

Because the proxy preserves the public API shape, existing applications continue
working. The only runtime change is pointing the app at the proxy and supplying
the sentinel key.

## 2. Migration Playbook (API → Direct CLI)

The following checklist can be handed to another model or developer. It
summarises the safest path for converting a program that currently calls an LLM
via REST into one that uses the local CLI tooling directly.

1. **Audit current usage**
   - Locate every module that instantiates the Anthropic or OpenAI client. Keep
     track of the request payload fields (model, messages, temperature, etc.).

2. **Introduce the local router**
   - Add the `anthropic_router.create_client` or `openai_router.create_client`
     helper provided by this repo. These helpers wrap the logic that decides
     between cloud and local execution.
   - If you must work in another language, start the HTTP proxy (`start_proxy.py`
     or `start_proxy.sh`) and point your application's HTTP(S) proxy settings to
     `http://localhost:8080`.

3. **Swap authentication for sentinel keys**
   - Replace the real API key with `999999999999` in environment variables or
     client configuration. The routers treat this value as "use the local CLI".

4. **Ensure CLI logins are complete**
   - Run `claude login` (for Claude Max) or `codex login` / `openai login` (for
     Codex Pro) once per machine. The CLI stores the session token locally so
     subsequent subprocess invocations succeed without embedding an API key in
     your program.

5. **Map unsupported parameters**
   - Some REST parameters (e.g., fine-grained tool invocation, JSON schema) may
     not exist in the CLI. Use the `_format_messages_for_claude` logic as a
     reference for how to collapse `messages` into plain text. Unsupported
     fields should be removed or emulated before calling the CLI.

6. **Test**
   - Execute the program and verify that the CLI outputs are parsed back into the
     expected `Message` objects. Unit tests such as `test_router.py` demonstrate
     the expected behaviours.

## 3. Specification for Direct CLI Invocation

The table below documents the input/output contracts, constraints, and required
preconditions when your program talks to the CLI without using the proxy. You
can embed this in another project's docs or task description.

### 3.1 Preconditions

| Requirement | Details |
|-------------|---------|
| User account | Active Claude Max subscription (for `claude` CLI) or ChatGPT Pro / Codex plan (for `codex` CLI). |
| Local tooling | `claude` CLI ≥ 0.6 or `codex` CLI ≥ 1.0 installed and available on `$PATH`. |
| Auth session | `claude login` or `codex login` must have been executed interactively beforehand. |
| Runtime      | Ability to spawn subprocesses and pipe stdin/stdout (POSIX shell or Windows PowerShell). |

### 3.2 Input Contract

| Field | Claude CLI | Codex CLI |
|-------|------------|-----------|
| Prompt encoding | UTF-8 text written to stdin. The helper in `ClaudeCodeClient._format_messages_for_claude` shows how to join `messages` into an instruction-following transcript (`Human:` / `Assistant:` markers). | UTF-8 text written to stdin. Use a simple instruction-response block (`User:` / `Assistant:`) or follow OpenAI CLI docs. |
| Model selection | Optional `--model` flag (`opus`, `sonnet`, `haiku`). Map REST IDs like `claude-3-5-sonnet-20241022` to the closest CLI alias. | Optional `--model` flag (e.g., `gpt-4.1`, `o4-mini`). |
| Max tokens | Not directly configurable. The CLI obeys built-in limits, so callers should truncate prompts. | Use `--max-output-tokens` if supported; otherwise rely on defaults. |
| Temperature | Not exposed. Consider post-processing or prompt engineering. | Some CLI builds expose `--temperature`; validate before use. |

### 3.3 Output Contract

| Property | Description |
|----------|-------------|
| Stream behaviour | Current router assumes non-streaming output. The CLI prints the entire completion to stdout and exits. |
| Format | Plain text response. The router wraps it inside Anthropic's `Message` (`content` → `[{"type": "text", "text": ...}]`). |
| Error handling | Non-zero exit codes correspond to CLI failure. Capture stderr for diagnostics and translate into exceptions (see `utils.CLINotFoundError`, `CLIError`). |

### 3.4 Constraints & Considerations

- **Rate limits**: The CLI enforces the same entitlements as the GUI. Exceeding
  limits returns an error message on stderr; no HTTP status codes are produced.
- **Concurrency**: Launching multiple CLI processes in parallel is possible but
  may hit local rate limits sooner. Implement a queue if deterministic ordering
  is required.
- **Prompt size**: Because everything is piped through stdin, stay well below the
  OS pipe buffer (generally <1 MB). For larger contexts write to a temp file and
  pass `--input-file` if the CLI supports it.
- **Security**: Session tokens stored by the CLI inherit the operating system's
  file permissions. Do not run the CLI under untrusted accounts.

### 3.5 Example Wrapper (Pseudo-code)

```python
from subprocess import run, PIPE, CalledProcessError

PROMPT_TEMPLATE = """System: {system}\n\nHuman: {user}\n\nAssistant:"""

def call_claude_cli(user_text: str, system: str = "") -> str:
    prompt = PROMPT_TEMPLATE.format(system=system, user=user_text)
    try:
        result = run(
            ["claude", "--print", "--model", "sonnet"],
            input=prompt.encode("utf-8"),
            stdout=PIPE,
            stderr=PIPE,
            check=True,
            timeout=120,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Claude CLI is not installed") from exc
    except CalledProcessError as exc:
        raise RuntimeError(f"Claude CLI failed: {exc.stderr.decode()}") from exc
    return result.stdout.decode("utf-8").strip()
```

The Codex wrapper is analogous; swap the executable name and flag set.

## 4. Getting Data In and Out Without API Keys

Because authentication lives in the CLI's cached session, your program never
handles raw API keys. The only data exchange required is:

1. **Input**: write the formatted prompt to the CLI's stdin. Include your entire
   conversation state in the prompt since the CLI is stateless between
   invocations.
2. **Output**: read stdout to capture the model's response. Parse or post-process
   as needed for your application.
3. **Metadata**: if you need token usage or latency metrics you must compute them
   yourself (e.g., word counts) because the CLI does not emit structured JSON.

For teams that require an SDK-like contract, reuse the conversion logic in
`claude_code_client.py` and `codex_client.py` to package the CLI result inside an
object that mimics the official API responses. That provides backward-compatible
interfaces while avoiding API key handling altogether.

## 5. Summary Checklist for Automation

1. Verify the user has run the vendor CLI `login` flow.
2. Replace REST client initialisation with the router or direct CLI wrapper.
3. Convert `messages` arrays into plain-text transcripts before invoking the CLI.
4. Capture stdout as the assistant response; map stderr/exit codes to errors.
5. Maintain your own rate limiting, retries, and metrics because the CLI exposes
   minimal diagnostics.

Following this specification keeps your program compliant with the vendors'
licensing, avoids storing API keys, and leverages the local CLI that ships with
Claude Max and ChatGPT Pro plans.
