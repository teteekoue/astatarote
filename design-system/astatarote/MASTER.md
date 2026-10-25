# Design System — Astatarote (SaaS)

> Généré avec le skill **ui-ux-pro-max** (recherches `--design-system`, `--domain style`, `--domain typography`).
> Sources : styles « Dark Mode (OLED) » + « Real-Time / Operations Landing », pairing « Developer Mono » / « Modern Dark Cinema ».

## Direction

Plateforme SaaS d'apprentissage Linux & cybersécurité — **professionnelle, élégante, technique**.
Sombre par défaut (mode unique assumé, comme un outil de dev/sécu), accents indigo (produit) et
émeraude (terminal/succès), statuts verts/orange/rouges façon console d'ops. Pas de néon
cyberpunk, pas de gimmick : densité maîtrisée, lisibilité, contraste AAA sur le texte courant.

## Pattern (parcours utilisateur)

1. **Landing publique** — hero + aperçu produit (terminal animé) + grille de parcours + CTA.
2. **Auth** — login / registre, visuel sobre, valeur rappelée en un mot.
3. **Catalogue** — cartes parcours figés : niveau, durée, compétences, points, progression perso.
4. **Dashboard** — mes parcours, progression, stats (points, rang, badges).
5. **Atelier de jeu** — 3 zones : mission (consigne + fiches + objectifs), terminal, assistante IA.

## Couleurs (tokens CSS)

| Rôle | Valeur | Usage |
|------|--------|-------|
| `--bg` | `#0A0F1E` | fond page (minuit profond) |
| `--surface` | `#101731` | cartes, panneaux |
| `--surface-2` | `#161F3D` | surfaces élevées, hover |
| `--border` | `#232D4D` | bordures, séparateurs |
| `--fg` | `#E6EAF4` | texte principal |
| `--muted` | `#8C97B4` | texte secondaire (contraste ≥ 4.5:1 sur surface) |
| `--primary` | `#6366F1` | actions principales (indigo) |
| `--primary-hover` | `#818CF8` | hover principal |
| `--accent` | `#10B981` | terminal, succès, badges (émeraude) |
| `--warning` | `#F59E0B` | avertissements, attention |
| `--danger` | `#EF4444` | erreurs, destructif |

## Typographie

- **UI** : Inter (400/500/600/700/800) — titres 800 -0.02em, corps 400 16px/1.55.
- **Mono** : JetBrains Mono (400/500/700) — terminal, code inline, badges techniques.
- Échelle : display 40-56, h1 30, h2 22, h3 17, body 15-16, small 13, micro 11 (uppercase +1.2 tracking pour labels).

## Espacements & rayons

- Scale 4/8/12/16/24/32/48/64. Cards `rounded-2xl`, boutons/inputs `rounded-xl`, chips `rounded-lg`.
- Ombres douces uniquement (pas de glow néon) ; focus visible `ring-2 ring-primary/60`.

## Composants clés

- **Boutons** : primary (indigo plein), secondary (surface + border), ghost, danger. 150-250ms transitions.
- **Cartes parcours** : icône domaine, tag niveau, durée, points, barre de progression fine.
- **Terminal** : panneau mono, header avec points d'état, prompt émeraude.
- **Chat IA** : bulles différenciées, avatar "N", markdown simple rendu (gras, listes, code).

## Règles anti-patterns (interdites)

- ❌ Emojis comme icônes → uniquement Lucide (SVG).
- ❌ Néon/glow excessif, glitch, scanlines.
- ❌ Texte < 12px, gris sur gris, hex bruts dans les composants (toujours les tokens).
- ❌ Hover sans état, focus invisible, transitions > 300ms.
- ❌ Placeholder comme seul label de champ de formulaire.

## Checklist pre-delivery (ui-ux-pro-max)

- [x] Icônes SVG (Lucide) uniquement
- [x] `cursor-pointer` sur tout élément cliquable
- [x] Hover states 150-300ms partout
- [x] Contraste texte ≥ 4.5:1
- [x] Focus clavier visible
- [x] Responsive 375 / 768 / 1024 / 1440
- [x] `prefers-reduced-motion` respecté (pas d'animation essentielle à la compréhension)
