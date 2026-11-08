# Glossary

This glossary is for Pascal designing a brigade.

## Roles

| Name | Why this name | Renamed from |
|---|---|---|
| Executive Chef | The user as a CTO. Oversees several kitchens, one Chef per project. Not in arancini | New |
| Product Manager | The user managing one project. Decides what to build and why, and has the last word | Not renamed. The user, USER in the CU diagrams |
| Head Chef | Bridges needs and requirements, splits batches and guides Chefs. In carpaccio, dolma, escargot and falafel, holds a merge only when the merge rule in Decisions is not met. In falafel, also creates each Cook's worktree and launches its Cook. Not in arancini | New |
| Chef | In bisque, carpaccio, dolma and escargot, coordinates a batch for the Head Chef. In carpaccio, launches Cooks and prevents conflicts between them; in dolma and escargot, launches the batch's one Cook. In each, validates, merges, releases and closes. Not in falafel | MAIN |
| Cook<n> | Owns its worktree and stack. In carpaccio, dolma, escargot and falafel, also writes docs, watches PRs, delegates reviews and triages findings. In dolma, escargot and falafel, one Cook implements every card of its batch. In falafel, also merges, releases and closes its batch | COD<n> |
| Watchdog | A Head Chef's or Chef's hidden delegate, scheduled in its own thread to wake or report stalled and failed work in carpaccio, dolma, escargot and falafel; in falafel, the Head Chef's only | New |
| DocWriter<n> | Writes docs in arancini and bisque; not in carpaccio, dolma, escargot or falafel | DOC<n> |

## Barrages

| Barrage | What it checks | Replaces |
|---|---|---|
| manic-1 | Every change in the stack, looking for a reason to reject it or anything overkill. In falafel, an angle of loop 1 on each PR | ADV<n> |
| manic-2 | What the stack could break. Includes a premortem that assumes it merged and broke something a week later. In falafel, an angle of loop 1 on each PR | BLAST<n> |
| manic-3 | Whether the docs match the changed behavior. In falafel, an angle of loop 2 on the whole stack | RDOC<n> |
| manic-4 | Nothing. It was never built, because of a design miscalculation. `$brigade ; <route> ; manic-4` runs the route in fast track: the Cook implements, and no DocWriter or barrage runs; in falafel, no docs step or loop runs | fast track |
| manic-5 | Polishes the final stack: duplication, misleading names or comments, heavy helpers, implementation-bound tests and scattered rules. In falafel, an angle of loop 2 on the whole stack | PRIS<n> |

## Courses

Each use case takes one course. Each version of a use case takes the next unused name of its course, in alphabetical order. A name becomes a route only when its playbook folder exists. The courses follow the order of a French meal.

| Course | Use case | Active | Reserved names |
|---|---|---|---|
| appetizers | CU1 | arancini, bisque, carpaccio, dolma, escargot, falafel | gravlax, halloumi, involtini, minestrone, nachos, onigiri, pakora, quiche, rillettes, sashimi, tartare, vichyssoise, wonton, yakitori |
| mains | Not assigned | None | alfredo, bourguignon, cassoulet, enchilada, fondue, gnocchi, jambalaya, kebab, linguine, moussaka, poutine, quesadilla, ratatouille, souvlaki, teriyaki, udon, vindaloo, wellington, yakisoba |
| cheeses | Not assigned | None | asiago, brie, burrata, camembert, cheddar, edam, emmental, fontina, gouda, havarti, manchego, mozzarella, oka, parmesan, provolone, raclette, ricotta, roquefort, stilton, taleggio |
| desserts | Not assigned | None | affogato, baklava, brownie, cannoli, clafoutis, dacquoise, financier, flan, gelato, halva, macaron, madeleine, meringue, nougat, pavlova, profiterole, religieuse, sabayon, tiramisu, vacherin |
