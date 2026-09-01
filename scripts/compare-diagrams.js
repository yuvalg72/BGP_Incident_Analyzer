const crypto = require("node:crypto");
const path = require("node:path");
const sharp = require("sharp");

const root = path.resolve(__dirname, "..");
const generatedDir = process.argv[2];
const diagrams = ["architecture", "analysis-flow"];

if (!generatedDir) {
  process.stderr.write("Usage: node scripts/compare-diagrams.js <generated-directory>\n");
  process.exit(2);
}

async function pixelDigest(file) {
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  return {
    width: info.width,
    height: info.height,
    channels: info.channels,
    digest: crypto.createHash("sha256").update(data).digest("hex"),
  };
}

Promise.all(diagrams.map(async (name) => {
  const committed = await pixelDigest(path.join(root, "docs", "images", `${name}.png`));
  const generated = await pixelDigest(path.join(generatedDir, `${name}.png`));
  if (JSON.stringify(committed) !== JSON.stringify(generated)) {
    throw new Error(`${name}.png does not visually match its SVG source`);
  }
  process.stdout.write(`Verified ${name}.png (${committed.width}x${committed.height})\n`);
})).catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});

