# Glossary

This glossary is for the user designing a brigade. The Chef does not need it, and SKILL.md does not link to it.

## Roles

| Name | Why this name | Renamed from |
|---|---|---|
| Executive Chef | The user as a CTO. Oversees several kitchens, one Chef per project. Not in arancini | New |
| Product Manager | The user managing one project. Decides what to build and why, and has the last word | Not renamed. The user, USER in the CU diagrams |
| Head Chef | Runs the pass for a whole run: splits the plan into batches, gives each one to a Chef, and green-lights each merge. The only thread the user talks to in bisque. Not in arancini | New |
| Chef | Runs the kitchen and never cooks. In bisque, runs one batch for the Head Chef | MAIN |
| Cook<n> | Cooks one card at its own station, its worktrees | COD<n> |
| DocWriter<n> | Writes the docs that describe the new dish | DOC<n> |
| Server | Takes what the kitchen made to the people it is for: changelog, version, tag, release. Not in arancini yet | New |

## Barrages

| Barrage | What it checks | Replaces |
|---|---|---|
| manic-1 | Every change in the stack, looking for a reason to reject it or anything overkill | ADV<n> |
| manic-2 | What the stack could break. Includes a premortem that assumes it merged and broke something a week later | BLAST<n> |
| manic-3 | Whether the docs match the changed behavior | RDOC<n> |
| manic-4 | Nothing. It was never built, because of a design miscalculation. `$brigade ; <route> ; manic-4` runs the route in fast track: the Cook implements, and no DocWriter or barrage runs | fast track |
| manic-5 | The whole stack one last time. It works, so what would make it great and simple | PRIS<n> |

## Courses

Each use case takes one course. Each version of a use case takes the next unused name of its course, in alphabetical order. A name becomes a route only when its playbook folder exists. The courses follow the order of a French meal.

| Course | Use case | Active | Reserved names |
|---|---|---|---|
| appetizers | CU1 | arancini, bisque | carpaccio, dolma, escargot, falafel, gravlax, halloumi, involtini, minestrone, nachos, onigiri, pakora, quiche, rillettes, sashimi, tartare, vichyssoise, wonton, yakitori |
| mains | Not assigned | None | alfredo, bourguignon, cassoulet, enchilada, fondue, gnocchi, jambalaya, kebab, linguine, moussaka, poutine, quesadilla, ratatouille, souvlaki, teriyaki, udon, vindaloo, wellington, yakisoba |
| cheeses | Not assigned | None | asiago, brie, burrata, camembert, cheddar, edam, emmental, fontina, gouda, havarti, manchego, mozzarella, oka, parmesan, provolone, raclette, ricotta, roquefort, stilton, taleggio |
| desserts | Not assigned | None | affogato, baklava, brownie, cannoli, clafoutis, dacquoise, financier, flan, gelato, halva, macaron, madeleine, meringue, nougat, pavlova, profiterole, religieuse, sabayon, tiramisu, vacherin |
