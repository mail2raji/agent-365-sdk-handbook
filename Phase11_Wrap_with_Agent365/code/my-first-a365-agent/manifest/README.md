# Manifest icons

Drop two PNG files in this folder before running `a365 publish`:

| File | Size | Notes |
|---|---|---|
| `color.png` | **192 × 192** | The full-colour app icon. Should be square, transparent background recommended. |
| `outline.png` | **32 × 32** | A monochrome white outline on transparent background. This is what Teams shows in the activity bar. |

If you don't have icons yet you can grab free placeholders from <https://icons8.com> or generate them with the Teams Toolkit:

```powershell
npm install -g @microsoft/teamsfx-cli
teamsfx generate-icons --output ./manifest
```

> ✋ Do not check production icons into a public repository if your organisation has branding restrictions.
