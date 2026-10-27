// node web/watch/test.mjs: the parser against a saved Gazette page
import fs from "node:fs";
import assert from "node:assert";
import { reinstated } from "./index.js";
const page = fs.readFileSync(process.argv[2], "utf8");
const got = reinstated(page);
assert(got.length > 0 && got.every(n => /^\d{7,8}$/.test(n)), "no reinstated numbers parsed");
console.log(got.length, "reinstated, e.g.", got.slice(0, 3).join(", "));
