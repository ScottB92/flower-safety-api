from flask import Flask, request, jsonify
import openai
import os
from difflib import get_close_matches
from functools import lru_cache
from tenacity import retry, wait_random_exponential, stop_after_attempt
import inflect
p = inflect.engine()

// At the top of your API route file
export default async function handler(req, res) {
  // Add CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*'); // Or specify domains
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  // Handle preflight request
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  // Your existing code here...
}


plural_map = {
    "lily": "lilies",
    "peony": "peonies",
    "daisy": "daisies",
    "cactus": "cacti"  # optional examples
}

app = Flask(__name__)

# 🔑 Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🌸 Flower safety dictionaries
SAFE_FLOWERS = {
    "Astilbe": "✅ Astilbe is totally safe for both cats and dogs to enjoy around the home.",
    "Erica": "✅ Erica is pet-friendly and safe for both cats and dogs.",
    "Freesia": "✅ Freesias are safe for cats and dogs – their sweet scent is safe for all.",
    "Greenbell": "✅ Greenbell is safe for both cats and dogs, so no worries if they get curious.",
    "Lisianthus": "✅ Lisianthus is safe for cats and dogs – delicate, but pet-friendly.",
    "Limonium": "✅ Limonium is perfectly safe for cats and dogs.",
    "Olive": "✅ Olive is safe for both cats and dogs, a lovely non-toxic choice.",
    "Pitto": "✅ Pitto is non-toxic and safe for both cats and dogs.",
    "Pussy willow": "✅ Pussy willow is safe for cats and dogs – a gentle, pet-friendly option.",
    "Roses": "✅ Roses are safe for cats and dogs (just watch out for thorns!).",
    "Snapdragons": "✅ Snapdragons are safe for both cats and dogs – bright and harmless.",
    "Statice": "✅ Statice is safe for cats and dogs, adding colour without worry.",
    "Stock": "✅ Stock is safe for cats and dogs – safe, sweet, and cheerful.",
    "Veronica": "✅ Veronica is pet-safe for both cats and dogs.",
    "Sunflowers": "✅ Sunflowers are safe for both cats and dogs – sunny and non-toxic.",
    "Waxflower": "✅ Waxflower is safe for cats and dogs.",
    "Trachelium": "🤔 Trachelium is safe for cats, but not recommended for dogs."
}

TOXIC_FLOWERS = {
    "Alstroemeria": "🤔 Alstroemeria is toxic to cats, but not listed as harmful for dogs.",
    "Astrantia": "⚠️ Astrantia is toxic to both cats and dogs.",
    "Asparagus Fern": "⚠️ Asparagus Fern is toxic to cats and dogs.",
    "Bupleurum": "⚠️ Bupleurum is toxic to both cats and dogs.",
    "Campanula bells": "⚠️ Campanula bells are toxic to cats and dogs.",
    "Clematis": "⚠️ Clematis is toxic to cats and dogs.",
    "Craspedia": "⚠️ Craspedia is toxic to cats and dogs.",
    "Delphinium": "⚠️ Delphinium is toxic to cats and dogs.",
    "Eucalyptus": "⚠️ Eucalyptus is toxic to cats and dogs.",
    "Erngium": "⚠️ Erngium is toxic to cats and dogs.",
    "Lavender": "⚠️ Lavender is toxic to cats and dogs.",
    "Lilies": "🤔 Lilies are extremely toxic to cats, but not listed as harmful for dogs.",
    "Ornithogalum": "⚠️ Ornithogalum is toxic to cats and dogs.",
    "Peonies": "⚠️ Peonies are toxic to cats and dogs.",
    "Ranunculus": "⚠️ Ranunculus is toxic to cats and dogs.",
    "Ruscus": "⚠️ Ruscus is toxic to cats and dogs.",
    "Senecio": "⚠️ Senecio is toxic to cats and dogs.",
    "September": "⚠️ September flowers are toxic to cats and dogs.",
    "Solidago": "⚠️ Solidago is toxic to cats and dogs.",
    "Solomio": "⚠️ Solomio is toxic to cats and dogs.",
    "Sweet William": "⚠️ Sweet William is toxic to cats and dogs.",
    "Tulip": "⚠️ Tulips are toxic to cats and dogs."
}

# 🌼 Combined dictionary for quick lookup
FLOWERS = {**{k.lower(): v for k, v in SAFE_FLOWERS.items()},
           **{k.lower(): v for k, v in TOXIC_FLOWERS.items()}}

# 🌸 Retry wrapper for OpenAI API (handles transient failures)
@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(3))
def ask_openai(messages):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

# 🌺 Cache AI lookups for unknown flowers
@lru_cache(maxsize=100)
def get_flower_safety(flower):
    try:
        # Step 1: Check if it's a real flower
        ai_prompt = f"Is '{flower}' a real flower or plant name? Answer only 'yes' or 'no'."
        ai_reply = ask_openai([{"role": "user", "content": ai_prompt}]).lower()

        if "no" in ai_reply:
            return "🌸 I’m a flower safety chatbot – please ask me about flowers only."

        # Step 2: Ask about pet safety
        safety_prompt = (
            f"Is the flower '{flower}' safe for cats and dogs? "
            "Answer in one or two clear sentences. "
            "If unsure, say you're unsure and recommend consulting a vet. "
            "Include a note: '(This information was generated by AI and has not been verified by experts.)'"
        )
        safety_reply = ask_openai([{"role": "user", "content": safety_prompt}])
        return safety_reply

    except Exception as e:
        print("OpenAI error:", e)
        return "⚠️ Sorry, there was a problem checking this flower’s safety."

@app.route("/flower-check", methods=["POST"])
def flower_check():
    data = request.get_json()
    flower = data.get("flower", "").strip()

    # Validate input
    if not flower or len(flower.split()) > 3 or not any(c.isalpha() for c in flower):
        return jsonify({"response": "🌸 I’m a flower safety chatbot – please ask me about flowers only."})

    # Lowercase the input
    flower_key = flower.lower()

    # Step 1: check manual plural map first
    used_plural_map = False
    if flower_key in plural_map:
        flower_key = plural_map[flower_key]
        used_plural_map = True

    # Step 2: singularize remaining plurals only if we didn't already use the plural map
    if not used_plural_map:
        singular = p.singular_noun(flower_key)
        if singular:
            flower_key = singular

    # Step 3: fuzzy match against dataset
    all_flowers = list(FLOWERS.keys())
    match = get_close_matches(flower_key, all_flowers, n=1, cutoff=0.7)
    if match:
        print(f"[DEBUG] Matched '{flower}' → '{match[0]}'")
        return jsonify({"response": FLOWERS[match[0]]})

    # Unknown flower → ask AI
    ai_response = get_flower_safety(flower)
    return jsonify({"response": ai_response})

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "🌸 Flower Safety API is running.",
        "usage": "Send a POST request to /flower-check with JSON like {'flower': 'Roses'}"
    })

if __name__ == "__main__":
    # 🔒 Don't use debug mode in production
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=False)
