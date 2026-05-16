# ezlx-skills

[中文](README.md)

Agent Skills & tools collection, maintained by the ezlx team.

## Quick Install

### Windows (PowerShell)

```powershell
curl -fsSL https://raw.githubusercontent.com/caofei277/ezlx-skills/main/install.ps1 | pwsh
```

### macOS / Linux (Bash)

```bash
curl -fsSL https://raw.githubusercontent.com/caofei277/ezlx-skills/main/install.sh | bash
```

Skills are installed to `~/.config/opencode/skills/` (globally available).

## Available Skills

### opencode-cross-platform-setup

Install and configure [OpenCode](https://opencode.ai) on Windows / macOS / Linux, including multiple Coding Plan Providers and MCP integration.

**Features**:
- Auto-detect platform (Windows / macOS / Linux)
- Install opencode-ai via npm
- Configure OpenCode Go (built-in provider, via `/connect` command)
- Configure Zhipu Coding Plan / Alibaba Cloud Bailian Coding Plan providers
- Configure MCP Puppeteer
- Guide API key setup (environment variable persistence)

**Supported Providers**:

| Provider | SDK | Models |
|----------|-----|--------|
| OpenCode Go | Built-in (auto-routing) | GLM-5.1, DeepSeek V4 Flash/Pro, Qwen3.6 Plus, Kimi K2.6 and more (12 total) |
| Zhipu Coding Plan | @ai-sdk/openai-compatible | GLM-5, GLM-5 Turbo, GLM-4.7, GLM-5.1 |
| Alibaba Bailian Coding Plan | @ai-sdk/anthropic | Qwen3.5 Plus, Qwen3.6 Plus, GLM-5, Kimi K2.5 and more (9 total) |

### opencode-update

Safely update OpenCode to the latest version, handling macOS code signing, npm prefix conflicts, network issues (GFW), and other common update failures.

**Features**:
- Auto-detect current opencode installation method, version, and network environment
- Prioritize GitHub mirror acceleration in GFW environments (ghfast.top etc.)
- Multiple update methods: mirror > proxy > npm > direct
- Download integrity verification (prevents silent corruption by GFW)
- macOS code signing fix (resolves `zsh: killed`)
- npm global prefix conflict detection and workaround
- Old version backup and rollback

**Common Issues Resolved**:

| Issue | Cause |
|-------|-------|
| `zsh: killed opencode` | macOS code signature invalid |
| npm update succeeded but version unchanged | npm prefix overridden by another app |
| `curl: (35) Connection reset` | GFW interfering with GitHub connection |
| Download completed but file corrupted | GFW silently truncating download, curl reports no error |

### Install Specific Skills

```bash
# Install a single skill
bash install.sh opencode-update

# Install multiple skills
bash install.sh opencode-cross-platform-setup opencode-update
```

## Manual Install

```bash
git clone https://github.com/caofei277/ezlx-skills.git
mkdir -p ~/.config/opencode/skills
cp -r ezlx-skills/skills/* ~/.config/opencode/skills/
```

## License

[MIT](LICENSE)
