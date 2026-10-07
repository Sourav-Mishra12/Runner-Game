# Replaceable environment art

Add optional transparent PNG layers inside `day/`, `sunset/`, `night/`, or `ruins/`.
Each region can override these generated parallax layers:

- `sky.png`
- `clouds.png`
- `mountains.png`
- `trees.png`
- `foreground.png`

The parallax loader caches each image at startup. Missing images use generated shapes, so no art is required to play. The sky still receives the gradual day-to-night tint. Rain, fog, snow, birds, and lightning are drawn as lightweight effects and also have procedural fallbacks.
