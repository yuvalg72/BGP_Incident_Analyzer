const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const sharp = require("sharp");

const root = path.resolve(__dirname, "..");
const sourceDir = path.join(root, "docs", "images");
const outputDir = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.join(os.tmpdir(), "bgp-diagrams");
const diagrams = ["architecture", "analysis-flow"];

fs.mkdirSync(outputDir, { recursive: true });

Promise.all(diagrams.map(async (name) => {
  const source = path.join(sourceDir, `${name}.svg`);
  const output = path.join(outputDir, `${name}.png`);
  await sharp(source, { density: 144 })
    .flatten({ background: "#ffffff" })
    .resize({ width: 1000, withoutEnlargement: false })
    .png({
      compressionLevel: 9,
      adaptiveFiltering: false,
      palette: true,
      colours: 64,
      dither: 0,
    })
    .toFile(output);
  process.stdout.write(`Rendered ${output}\n`);
})).catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
