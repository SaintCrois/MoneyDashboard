# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React + TypeScript on Vite, in `web/`. Chosen by Pentor on 2026-11-14 ("React / Next.js"); Vite was picked over Next.js because the app is a client-side view over the existing FastAPI backend and needs no server rendering. The Streamlit dashboard in `client/` stays as the team's internal tool.

## Users

First-time Thai retail investors aged about 18 to 25 who already hold a few Thai stocks they bought because an investor they follow bought them. They see big news, know it relates to a stock they hold, but cannot judge how it affects the business.

## Product Purpose

WhyMove shows which recent news may relate to each stock the user holds, how that kind of event can affect the business on both the upside and the downside, what to check next, and the source. Success: the user understands why a stock may be moving before deciding anything.

## Positioning

It explains impact on the business with reasons and sources. It never tells the user to buy or sell.

## Operating Context

Built for the Trinity Securities Future Finance Innovation Hackathon 2026 (track: AI for Insight). Reading news and impact is free; alerts for held stocks are planned to require a Trinity account.

## Capabilities and Constraints

- News comes from RSS feeds (Thai and global, English). Only headline and short summary are read.
- The link between news and a company is keyword-level: ticker or company name (direct), or business-group keywords (indirect). Three strictness levels: strict, medium, loose.
- Scenario text per business group is prepared example copy, not AI output and not a verified conclusion.
- No AI is used in the current build. No prices, returns or confidence scores.
- Ten SET companies: PTT, PTTEP, GULF, IVL, AOT, SCB, KBANK, ADVANC, BDMS, CPALL.
- Alerts and the Trinity account link are not implemented.

## Brand Commitments

Working name: WhyMove. Team deck colours: orange #FF5728, light grey #E1E3E4, black, white.

## Evidence on Hand

Live news in the local PostgreSQL database. No user research beyond the team's own experience; do not invent user numbers or testimonials.

## Product Principles

1. Explain, never advise.
2. Every interpretation points to its source news.
3. Keep facts from the news and the system's interpretation visibly separate.
4. Say "not enough data" instead of guessing.

## Accessibility & Inclusion

Thai UI. Impact and link-type labels must not rely on colour alone. No gain/loss colouring.
