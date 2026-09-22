import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const csvPath = path.join(rootDir, "data", "members.csv");

function membersCsvPlugin() {
  function attach(server) {
    server.middlewares.use((req, res, next) => {
      const url = req.url?.split("?")[0];
      if (url !== "/data/members.csv") {
        next();
        return;
      }

      if (req.method === "GET") {
        res.setHeader("Content-Type", "text/csv; charset=utf-8");
        res.setHeader("Cache-Control", "no-store");
        res.end(fs.readFileSync(csvPath, "utf8"));
        return;
      }

      if (req.method === "PUT") {
        const chunks = [];
        req.on("data", (chunk) => chunks.push(chunk));
        req.on("end", () => {
          fs.writeFileSync(csvPath, Buffer.concat(chunks).toString("utf8"), "utf8");
          res.statusCode = 204;
          res.end();
        });
        return;
      }

      next();
    });
  }

  return {
    name: "members-csv-db",
    configureServer: attach,
    configurePreviewServer: attach,
  };
}

export default defineConfig({
  plugins: [react(), membersCsvPlugin()],
  server: { port: 5173 },
});
