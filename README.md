# ARIS — arisweare.com

A small, fast, static shop for ARIS. Customers choose a piece and a size, then tap
**Order on WhatsApp**, which opens a chat with the order already written out.
There is no database, no plugins and no admin login, so there is nothing to hack.

## Changing the shop

Everything about the products lives in **`products.json`**. You can edit it right on
GitHub (open the file, click the pencil, then *Commit changes*). The site rebuilds and
goes live by itself about a minute later.

| To…                          | Change in `products.json`                                  |
|------------------------------|------------------------------------------------------------|
| Change a price               | `"price": 49.95`                                           |
| Put something on sale        | set `"compare_at"` to the old price, e.g. `69.90` (`null` = no sale) |
| Mark something sold out      | `"in_stock": false`                                        |
| Change the sizes             | `"sizes": ["S", "M", "L"]`                                 |
| Change the WhatsApp number   | `"whatsapp"` under `shop` (country code, digits only)      |
| Add a product                | copy one product block, change it, and upload its photos to `assets/img/products/` |

Shipping, returns and privacy text are in the `content/` folder.

## Previewing on your computer

```bash
python3 build.py
python3 -m http.server -d _site 8000
```

Then open http://localhost:8000.

## Going live on arisweare.com

1. In the repository on GitHub: **Settings → Pages → Source: GitHub Actions**.
2. Add a file named `CNAME` containing `arisweare.com`.
3. At the domain's DNS (Hostinger → Domains → DNS), point `arisweare.com` to GitHub Pages:
   four `A` records `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`,
   and a `CNAME` record for `www` pointing to `<your-github-username>.github.io`.
4. Back in **Settings → Pages**, tick **Enforce HTTPS** once it becomes available.
