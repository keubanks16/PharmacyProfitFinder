# Pharmacy Profit Finder

A phone-friendly, single-page tool for independent pharmacies. It combines three files the pharmacy already has:

1. **Paid claims export** (CSV): what each plan actually paid for each NDC
2. **NADAC** (CSV from CMS, updated weekly): the national average acquisition cost
3. **Wholesaler price file** (CSV): what the pharmacy pays

It shows:

- **Best NDC**: one recommendation per drug — the NDC to stock that makes the most across your whole plan mix, with a confidence level based on how much is real payment data
- **Switch NDCs**: for each drug + plan, which NDC left more profit per unit than the one dispensed most
- **Losing money**: drug + plan combos paid below cost, with MAC-appeal flags when paid below NADAC
- **Overpaying**: NDCs bought well above NADAC
- **Drug lookup**: paid / cost / profit per NDC by plan
- **Rejections**: plain-English explanations and fix steps for common NCPDP reject codes; tracks which fix worked for each plan (saved on the device). Optional "Ask AI" button talks to a local Ollama model, so no patient data leaves the store.

All files are read in the browser; nothing is uploaded anywhere. Sample (made-up) data loads by default.

## Ground rules
The tool only learns from real, dispensed, paid claims. It never suggests test claims or billing an NDC other than the one dispensed.

## NADAC data (automatic)
The **Update NADAC prices** GitHub Action (`.github/workflows/update-nadac.yml`) runs every Thursday after CMS posts new prices. It finds the newest yearly NADAC dataset on [data.medicaid.gov](https://data.medicaid.gov/dataset/fbb83258-11c7-47f5-8b18-5f8e79f7e704) (it switches to the 2027 dataset on its own), keeps the latest price per NDC, and commits `data/nadac.json`. The app loads that file automatically and shows which NDCs you use changed price that week.

Run it by hand any time from **Actions → Update NADAC prices → Run workflow**. You can still upload a NADAC CSV on the **Your data** tab to override it.

## Local AI (optional)
Install [Ollama](https://ollama.com) on a pharmacy PC, run `ollama pull llama3.1:8b`, and set `OLLAMA_ORIGINS` to this site's address (e.g. `https://keubanks16.github.io`). Open the tool from that PC and use **Rejections → Ask local AI**. Dates, long ID numbers and phone numbers are blanked out before anything is sent.
