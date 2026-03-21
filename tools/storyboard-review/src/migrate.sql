-- Migration: Add generation pipeline columns
-- Run via: npx wrangler d1 execute storyboard-review-db --file=src/migrate.sql
-- (add --local for local dev)

ALTER TABLE scenes ADD COLUMN hero_shot_url TEXT;
ALTER TABLE scenes ADD COLUMN character_refs TEXT;

ALTER TABLE panels ADD COLUMN scene_description TEXT;
ALTER TABLE panels ADD COLUMN motion_prompt TEXT;
