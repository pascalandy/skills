# Glossary

This glossary is for Pascal designing a brigade.

## Roles

| Name | Why this name | Renamed from |
|---|---|---|
| Executive Chef | The user as a CTO. Oversees several kitchens, one Chef per project. Not in arancini | New |
| Product Manager | The user managing one project. Decides what to build and why, and has the last word | Not renamed. The user, USER in the CU diagrams |
| Head Chef | Bridges needs and requirements, splits batches and guides Chefs. In carpaccio, holds merges only for Pascal's validation or low confidence. Not in arancini | New |
| Chef | In bisque and carpaccio, coordinates a batch for the Head Chef. In carpaccio, launches Cooks, prevents conflicts, validates, merges, releases and closes | MAIN |
| Cook<n> | Owns its worktree and stack. In carpaccio, also writes docs, watches PRs, delegates reviews and triages findings | COD<n> |
| DocWriter<n> | Writes docs in arancini and bisque; not in carpaccio | DOC<n> |

## Barrages

| Barrage | What it checks | Replaces |
|---|---|---|
| manic-1 | Every change in the stack, looking for a reason to reject it or anything overkill | ADV<n> |
| manic-2 | What the stack could break. Includes a premortem that assumes it merged and broke something a week later | BLAST<n> |
| manic-3 | Whether the docs match the changed behavior | RDOC<n> |
| manic-4 | Nothing. It was never built, because of a design miscalculation. `$brigade ; <route> ; manic-4` runs the route in fast track: the Cook implements, and no DocWriter or barrage runs | fast track |
| manic-5 | Polishes the final stack: duplication, misleading names or comments, heavy helpers, implementation-bound tests and scattered rules | PRIS<n> |

## Courses

Each use case takes one course. Each version of a use case takes the next unused name of its course, in alphabetical order. A name becomes a route only when its playbook folder exists. The courses follow the order of a French meal.

| Course | Use case | Active | Reserved names |
|---|---|---|---|
| appetizers | CU1 | arancini, bisque, carpaccio | dolma, escargot, falafel, gravlax, halloumi, involtini, minestrone, nachos, onigiri, pakora, quiche, rillettes, sashimi, tartare, vichyssoise, wonton, yakitori |
| mains | Not assigned | None | alfredo, bourguignon, cassoulet, enchilada, fondue, gnocchi, jambalaya, kebab, linguine, moussaka, poutine, quesadilla, ratatouille, souvlaki, teriyaki, udon, vindaloo, wellington, yakisoba |
| cheeses | Not assigned | None | asiago, brie, burrata, camembert, cheddar, edam, emmental, fontina, gouda, havarti, manchego, mozzarella, oka, parmesan, provolone, raclette, ricotta, roquefort, stilton, taleggio |
| desserts | Not assigned | None | affogato, baklava, brownie, cannoli, clafoutis, dacquoise, financier, flan, gelato, halva, macaron, madeleine, meringue, nougat, pavlova, profiterole, religieuse, sabayon, tiramisu, vacherin |
