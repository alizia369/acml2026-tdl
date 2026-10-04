# Topological Deep Learning tutorial, ACML 2026

Website for the tutorial "Topological Deep Learning for Robust Representation Learning: Foundations, Architectures, and Applications" (ACML 2026, Melbourne, 1 December 2026).

Plain HTML, CSS, and JavaScript. No build step and no dependencies.

## Publish on GitHub Pages

1. Create a public repository under `alizia369` named `acml2026-tdl`.
2. Upload everything in this folder to the repository root on `main` (keep the `assets` folder and the `.nojekyll` file).
3. Go to Settings, then Pages. Under "Build and deployment" choose "Deploy from a branch", select `main` and `/ (root)`, and save.
4. After a minute or two the site is live at https://alizia369.github.io/acml2026-tdl/

If you use a different repository name, update the three URLs near the top of `index.html` (`canonical`, `og:url`, `og:image`).

## Things to update

| What | Where |
|---|---|
| Session time and room | `index.html`: the "When" line in the hero, and the note under the programme |
| Presenter photos | Save square photos as `assets/img/ali-zia.jpg` and `assets/img/abdelwahed-khamis.jpg`, then change the two `src="assets/img/....svg"` attributes in the Presenters section to `.jpg` |
| Slides and worked examples | `index.html`, Materials section: replace the "Coming soon" label with a link |
| Extra presenter or links | Copy an `<article class="person">` block in the Presenters section |

## Files

- `index.html`: all page content, including the three inline SVG figures
- `assets/css/style.css`: styles
- `assets/js/filtration.js`: the interactive persistent homology figure in the hero. The simplices and persistence bars are precomputed and were checked against Ripser.
- `assets/img/`: favicon, social sharing card (`og.png`), presenter placeholders
- `tests/qa.py`: browser test suite (layout at five screen sizes, links, programme arithmetic, the interactive figure, keyboard use, optional axe accessibility audit)

## Run the tests

```
pip install playwright && playwright install chromium
python tests/qa.py
```
