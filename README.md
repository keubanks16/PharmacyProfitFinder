# Pharmacy Profit Finder

A phone-friendly, single-page tool for independent pharmacies. It combines three files the pharmacy already has:

1. **Paid claims export** (CSV): what each plan actually paid for each NDC
2. **NADAC** (CSV from CMS, updated weekly): the national average acquisition cost
3. **Wholesaler price file** (CSV): what the pharmacy pays

It shows:

- **Switch NDCs**: for each drug + plan, which NDC left more profit per unit than the one dispensed most
- **Losing money**: drug + plan combos paid below cost, with MAC-appeal flags when paid below NADAC
- **Overpaying**: NDCs bought well above NADAC
- **Drug lookup**: paid / cost / profit per NDC by plan

All files are read in the browser; nothing is uploaded anywhere. Sample (made-up) data loads by default.

## Ground rules
The tool only learns from real, dispensed, paid claims. It never suggests test claims or billing an NDC other than the one dispensed.

## NADAC data
Download the current CSV from [data.medicaid.gov](https://data.medicaid.gov/dataset/fbb83258-11c7-47f5-8b18-5f8e79f7e704) and load it on the **Your data** tab.
