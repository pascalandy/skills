const BOARD = {
  id: "mainline-opus",
  mount(el, br, ui) {
    const NS = "http://www.w3.org/2000/svg";
    const add = (parent, tag, attrs = {}, text) => {
      const node = document.createElementNS(NS, tag);
      for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
      if (text !== undefined) node.textContent = text;
      parent.append(node);
      return node;
    };
    const html = (parent, tag, cls, text) => {
      const node = document.createElement(tag);
      if (cls) node.className = cls;
      if (text !== undefined) node.textContent = text;
      parent.append(node);
      return node;
    };

    // One line-icon family on a 24-unit grid. Strokes stay 1.6 px at any scale
    const GLYPHS = [
      { line: ["M7.5 7.5 3 12l4.5 4.5", "M16.5 7.5 21 12l-4.5 4.5", "M14 5l-4 14"] }, // Implement: </>
      { line: ["M2 12c2.8-4.7 6.2-7 10-7s7.2 2.3 10 7c-2.8 4.7-6.2 7-10 7s-7.2-2.3-10-7Z"], dot: [12, 12, 3] }, // Review 1/2: an eye, the first look
      { line: ["M10.8 4.3a6.5 6.5 0 1 0 0 13 6.5 6.5 0 1 0 0-13Z", "M15.5 15.5 20.5 20.5"] }, // Review 2/2: a magnifier, the second and finer look
      { // Ship: a rocket, drawn upright and turned to climb to the right
        line: ["M12 4.5c3 2.3 4.2 5.9 3.6 10.5L15 18H9l-.6-3C7.8 10.4 9 6.8 12 4.5Z", "M8.6 14 5.8 16.4v3.2L9 18", "M15.4 14l2.8 2.4v3.2L15 18"],
        ring: [12, 11, 1.7], turn: 45, grow: 1.12, // a diagonal reads smaller than the upright glyphs
      },
    ];
    const D = 26; // badge diameter
    const icon = (parent, kind, cx, cy, size = D) => {
      const g = add(parent, "g", { class: "f2m-icon" });
      const tip = add(g, "title");
      const badge = add(g, "circle", { class: "f2m-badge", cx, cy, r: size / 2 - 0.75 });
      const spec = GLYPHS[kind], k = (size * 0.62 * (spec.grow || 1)) / 24;
      const at = add(g, "g", { transform: `translate(${cx - 12 * k} ${cy - 12 * k}) scale(${k})${spec.turn ? ` rotate(${spec.turn} 12 12)` : ""}` });
      const glyph = add(at, "g", { class: "glyph" });
      for (const d of spec.line) add(glyph, "path", { d });
      if (spec.ring) add(glyph, "circle", { cx: spec.ring[0], cy: spec.ring[1], r: spec.ring[2] });
      let fill = null;
      if (spec.dot) {
        fill = add(at, "g", { class: "glyph-fill" });
        add(fill, "circle", { cx: spec.dot[0], cy: spec.dot[1], r: spec.dot[2] });
      }
      return { tip, badge, glyph, fill };
    };
    const paintIcon = (it, word) => {
      ui.mark(it.badge, word.s);
      ui.mark(it.glyph, word.s);
      ui.mark(it.fill, word.s);
      it.tip.textContent = word.tip;
    };

    el.classList.add("f2m");
    el.innerHTML = `<style>
      .f2m .f2m-key { display: flex; flex-wrap: wrap; gap: 8px 24px; margin: 0 0 16px; padding: 0; list-style: none; font-size: 13px; line-height: 20px; color: var(--ink-2); }
      .f2m .f2m-key.f2m-two { display: grid; grid-template-columns: repeat(2, max-content); column-gap: 28px; }
      .f2m .f2m-key li { display: flex; align-items: center; gap: 8px; }
      .f2m .f2m-key svg { display: block; flex: none; }
      .f2m .f2m-grid { display: grid; gap: 16px; }
      .f2m .f2m-card { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 16px 20px 14px; min-width: 0; }
      .f2m .f2m-head { display: flex; align-items: baseline; gap: 10px; margin: 0 0 12px; min-height: 28px; }
      .f2m .f2m-tag { display: inline-block; font-size: 17px; font-weight: 700; line-height: 22px; padding: 2px 9px; border-radius: 6px; white-space: nowrap; }
      :where(.f2m .f2m-tag) { border-width: 1px; border-style: solid; } /* the state rules keep its border color and dash */
      .f2m .f2m-ref { font-size: 13px; color: var(--muted); white-space: nowrap; }
      .f2m .f2m-part { margin-left: auto; font-size: 12.5px; color: var(--muted); white-space: nowrap; }
      .f2m .f2m-graph { display: block; overflow: visible; font-family: inherit; }
      .f2m .f2m-rail { fill: none; stroke: var(--axis); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
      .f2m .f2m-badge { stroke-width: 1.5; }
      .f2m .glyph { stroke-dasharray: none; }
      .f2m .glyph * { vector-effect: non-scaling-stroke; }
      .f2m .f2m-cookmark { stroke-width: 1; }
      .f2m .f2m-cook { fill: var(--ink); font-size: 14px; font-weight: 700; }
      .f2m .f2m-stories { fill: var(--ink-2); font-size: 12.5px; }
      .f2m .f2m-key .f2m-badge { fill: none; stroke: var(--axis); }
      .f2m .f2m-key .glyph { fill: none; stroke: var(--ink-2); stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
      .f2m .f2m-key .glyph-fill { fill: var(--ink-2); }
    </style>`;

    const W = Math.max(1, Math.floor(el.clientWidth));

    // the key: each icon once, neutral, with its step title
    const key = html(el, "ul", "f2m-key");
    key.setAttribute("aria-label", "Step key");
    if (W < 520) key.classList.add("f2m-two");
    br.steps.forEach((title, i) => {
      const li = html(key, "li");
      const svg = add(li, "svg", { width: 24, height: 24, "aria-hidden": "true" });
      const it = icon(svg, i, 12, 12, 24);
      it.tip.remove();
      li.append(document.createTextNode(title));
    });

    // cards: at most four across, the run wraps down
    const gap = 16, minCard = 296; // the grid's gap in the CSS above
    const cols = Math.max(1, Math.min(4, Math.floor((W + gap) / (minCard + gap))));
    const grid = html(el, "div", "f2m-grid");
    grid.style.gridTemplateColumns = `repeat(${cols}, minmax(0, 1fr))`;
    const inner = Math.floor((W - gap * (cols - 1)) / cols) - 2 - 40;

    // the label column: Cook name over its Story count
    const ctx = document.createElement("canvas").getContext("2d");
    const family = getComputedStyle(el).fontFamily;
    const measure = (text, font) => { ctx.font = `${font} ${family}`; return ctx.measureText(text).width; };
    let label = 0;
    for (const id of Object.keys(br.cooks)) {
      const w = ui.say.cook(br, {}, id, br.start);
      label = Math.max(label, measure(w.name, "700 14px"), measure(w.stories, "400 12.5px"));
    }
    const LX = 16; // name and count start here; the Cook's mark hangs left of them
    // step pitch from what the card leaves: the Ship sits on the card's right edge, the reviews to its left
    const room = inner - LX - label - 18 - D - 16;
    const P = Math.max(34, Math.min(44, Math.floor(room / 3)));
    const Q = P + 16;
    const xS = inner - D / 2 - 1, x3 = xS - Q, xs = [x3 - 2 * P, x3 - P, x3];
    const xr = x3 + Q / 2, rr = 10; // where the other lines rise into the main line
    const ROW = 44, Y0 = ROW / 2;

    const parts = new Map();
    for (const b of br.batches) if (b.epic) parts.set(b.epic.n, (parts.get(b.epic.n) || 0) + 1);
    const seen = new Map();

    const epics = br.batches.map((batch) => {
      const card = html(grid, "article", "f2m-card");
      const ew = ui.say.epic(br, {}, batch, br.start);
      card.setAttribute("aria-label", [ew.name, ew.ref].filter(Boolean).join(" "));
      const head = html(card, "header", "f2m-head");
      const tag = html(head, "span", "f2m-tag", ew.name);
      if (ew.ref) html(head, "span", "f2m-ref", ew.ref);
      const total = batch.epic ? parts.get(batch.epic.n) : 1;
      if (total > 1) {
        const part = (seen.get(batch.epic.n) || 0) + 1;
        seen.set(batch.epic.n, part);
        html(head, "span", "f2m-part", `part ${part} of ${total}`);
      }

      const cooks = ui.cooksOf(br, batch);
      const n = Math.max(1, cooks.length);
      const svg = add(card, "svg", { class: "f2m-graph", width: inner, height: n * ROW, viewBox: `0 0 ${inner} ${n * ROW}` });
      const rails = add(svg, "g");
      const y = (i) => Y0 + i * ROW;
      // the first Cook's line is the main line: it alone runs on to Ship
      cooks.forEach((cook, i) => {
        const d = i === 0
          ? `M${xs[0]},${y(0)}H${xS}`
          : `M${xs[0]},${y(i)}H${xr - rr}A${rr},${rr} 0 0 0 ${xr},${y(i) - rr}V${y(0) + rr}A${rr},${rr} 0 0 1 ${xr + rr},${y(0)}`;
        add(rails, "path", { class: "f2m-rail", d });
      });
      const rows = cooks.map((cook, i) => {
        const cw = ui.say.cook(br, {}, cook.id, br.start);
        const mg = add(svg, "g");
        const tip = add(mg, "title");
        const mark = add(mg, "rect", { class: "f2m-cookmark", x: 0.5, y: y(i) - 11.5, width: 8, height: 8, rx: 2 });
        add(svg, "text", { class: "f2m-cook", x: LX, y: y(i) - 2 }, cw.name);
        add(svg, "text", { class: "f2m-stories", x: LX, y: y(i) + 14 }, cw.stories);
        const steps = xs.map((x, k) => icon(svg, k, x, y(i)));
        return { id: cook.id, mark, tip, steps };
      });
      const ship = icon(svg, 3, xS, y(0));
      return { batch, tag, ship, rows };
    });

    return {
      paint(st, t) {
        for (const e of epics) {
          const ew = ui.say.epic(br, st, e.batch, t);
          ui.mark(e.tag, ew.s);
          e.tag.title = ew.tip;
          paintIcon(e.ship, ui.say.ship(br, st, e.batch, t));
          for (const r of e.rows) {
            const cw = ui.say.cook(br, st, r.id, t);
            ui.mark(r.mark, cw.s);
            r.tip.textContent = cw.tip;
            r.steps.forEach((it, k) => paintIcon(it, ui.say.step(br, st, r.id, k + 1, t)));
          }
        }
      },
    };
  },
};
