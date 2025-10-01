# Studio Apps

This repository hosts public resources for our apps, including privacy policies and support pages.

## Apps

### DropBrain
Privacy-first note-taking designed for neurodivergent minds.

- **Privacy Policy:** [dropbrain/privacy_policy.html](dropbrain/privacy_policy.html)
- **App Store:** [Link to be added]

## Structure

```
/
├── index.html                    # Landing page for all apps
├── dropbrain/
│   ├── index.html               # DropBrain app page
│   └── privacy_policy.html      # DropBrain privacy policy
└── [future-app]/
    ├── index.html               # Future app page
    └── privacy_policy.html      # Future app privacy policy
```

## Adding a New App

1. Create a new directory: `mkdir newapp`
2. Add `newapp/privacy_policy.html`
3. Add `newapp/index.html` (optional landing page)
4. Update root `index.html` to list the new app

## GitHub Pages

This repository is set up for GitHub Pages. Each app's privacy policy will be available at:
- `https://[username].github.io/dropbrain-studio/[appname]/privacy_policy.html`

## Local Development

```bash
# Serve locally
python3 -m http.server 8000

# Visit
open http://localhost:8000
```

