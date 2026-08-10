"use strict";
// Steady-state timing of the Node HTML pretty-printers, so the comparison with the
// in-process Python tools excludes one-off Node startup (best-of repeats after a
// warm-up, mirroring Python's timeit). Reads {size: html} as JSON on stdin and
// writes {tool: {size: seconds_per_call}} as JSON on stdout.

const prettier = require("prettier");
const beautifyHtml = require("js-beautify").html;

const TOOLS = {
  prettier: (html) => prettier.format(html, { parser: "html" }),
  "js-beautify": (html) => beautifyHtml(html),
};

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

async function perCallSeconds(fn, html) {
  for (let i = 0; i < 3; i++) await fn(html); // warm up
  let number = 1;
  let elapsed = 0;
  while (elapsed < 0.2) {
    number *= 2;
    const start = process.hrtime.bigint();
    for (let i = 0; i < number; i++) await fn(html);
    elapsed = Number(process.hrtime.bigint() - start) / 1e9;
  }
  let best = Infinity;
  for (let repeat = 0; repeat < 5; repeat++) {
    const start = process.hrtime.bigint();
    for (let i = 0; i < number; i++) await fn(html);
    best = Math.min(best, Number(process.hrtime.bigint() - start) / 1e9 / number);
  }
  return best;
}

(async () => {
  const inputs = JSON.parse(await readStdin());
  const results = {};
  for (const [tool, fn] of Object.entries(TOOLS)) {
    results[tool] = {};
    for (const [size, html] of Object.entries(inputs)) {
      results[tool][size] = await perCallSeconds(fn, html);
    }
  }
  process.stdout.write(JSON.stringify(results));
})();
