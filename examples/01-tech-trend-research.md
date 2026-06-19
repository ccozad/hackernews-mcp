# Tech trend research

**Scenario:** survey recent discussion on a topic over a time window.
**Tools exercised:** `search_hackernews` with `time_range` and `sort`.

## Suggested prompt

> What's the discussion on AI been like in the past month?

## Claude's reasoning

Before the tool call

```
I need to search for recent HN discussions about AI from the past month. Since "AI" is pretty broad, I'll start with a date-sorted search to get a good sample of stories, and maybe also try a relevance-based search to see what's getting the most attention.
```

After the tool call
```
Looking at the dominant themes emerging from this month's stories, there's a clear pattern of consumer pushback against AI — from fatigue with AI-heavy messaging to concerns about plagiarism and preference for AI-free alternatives like DuckDuckGo.

Beyond the backlash, I'm seeing several other major threads: questions about whether AI actually improves coding productivity, stories of AI agents malfunctioning or causing real harm, the push for open source AI alternatives, regulatory developments around liability and labeling, and a broader debate about whether AI progress is actually slowing down or hitting a plateau. There are also some counter-narratives pushing back on the skepticism.

I think organizing these by theme rather than listing all the individual stories will make this clearer and more readable for the user.
```

## Tool call

```json
{
  "limit": 25,
  "query": "AI",
  "sort": "relevance",
  "tag": "story",
  "time_range": "past_month"
}
```

## Tool response (trimmed from 25 hits — representative sample)

```json
{
  "hits": [
    {
      "id": "48292224",
      "title": "I'm Tired of Talking to AI",
      "url": "https://orchidfiles.com/im-tired-of-ai-generated-answers/",
      "points": 2013,
      "author": "theorchid",
      "num_comments": 951,
      "created_at": "2026-05-27T10:43:25Z",
      "excerpt": "I'm Tired of Talking to <em>AI</em>"
    },
    {
      "id": "48511908",
      "title": "Open source AI must win",
      "url": "https://opensourceaimustwin.com/?share=v2",
      "points": 1599,
      "author": "vednig",
      "num_comments": 482,
      "created_at": "2026-06-13T02:14:24Z",
      "excerpt": "Open source <em>AI</em> must win"
    },
    {
      "id": "48500012",
      "title": "AI agent bankrupted their operator while trying to scan DN42",
      "url": "https://lantian.pub/en/article/fun/ai-agent-bankrupted-their-operator-scan-dn42lantian.lantian/",
      "points": 1466,
      "author": "xiaoyu2006",
      "num_comments": 534,
      "created_at": "2026-06-12T04:42:53Z",
      "excerpt": "<em>AI</em> agent bankrupted their operator while trying to scan DN42"
    }
  ]
}
```

## Claude's final answer

A clear picture emerges from the past month, and the dominant note is backlash and fatigue rather than hype. Here's how the discussion broke down.

**AI fatigue was the single biggest theme.** The month's top story by a wide margin was "I'm Tired of Talking to AI" (2,013 points, 951 comments), and it wasn't alone. "Sixty percent of US consumers say 'AI' in brand messaging is a turnoff" (1,074), a tool for detecting "AI-generated walls of text" thrown into conversations (717), and a report that DuckDuckGo's AI-free search saw nearly 28% more traffic right after Google insisted people love AI mode (1,075) all landed in the same vein. There was also a pointed "AI is just unauthorised plagiarism at a bigger scale" (824). The crowd is visibly tired of AI being pushed into everything.

**Agents going rogue was the month's most viral genre.** Three separate incidents drew huge attention: an AI agent that bankrupted its operator while trying to scan the DN42 network (1,466), an "AI agent runs amok in Fedora and elsewhere" writeup from LWN (552), and Meta confirming thousands of Instagram accounts were hacked by abusing its own AI chatbot (709). The throughline was autonomy outpacing guardrails.

**AI and coding/education stayed contentious.** "Using AI to write better code more slowly" (1,257) argued for a slower, more deliberate approach, while a UC Berkeley piece on failing grades climbing alongside AI use and dwindling math skills (834) fueled a 791-comment debate about what AI is doing to learning. Simon Willison's read on Uber's $1,500/month AI usage cap (624) anchored a discussion about what AI tooling actually costs.

**Legal and regulatory questions sharpened.** A German court ruled Google liable for false answers in its AI Overviews — treating them as Google's own words (1,020) — which many saw as a potential landmark. YouTube moving to auto-label AI-generated videos (1,322) and Adafruit receiving a legal demand letter on behalf of Flux.ai (684) rounded out the friction between AI products and existing rights.

**The "is it plateauing?" debate ran underneath all of it.** "AI is slowing down" (674) made the bubble/plateau case, and it's interesting to read against Anthropic's own post on progress toward recursive self-improvement (534) — the two framings sat on the front page the same week. "CEOs who think AI replaces their employees are just bad CEOs" (844) and a piece on tech CEOs suffering "AI psychosis" (722) reflected skepticism aimed squarely at executive hype.

**Big-tech moves and a few counter-takes filled out the month.** Apple revealing an AI architecture built around Google Gemini models (738) and the related "Siri AI" Apple Intelligence page (681) drew attention to Apple outsourcing its models. "Open source AI must win" (1,599) was the second-biggest story overall, a strong signal of where HN's sympathies lie. And not everything was sour: "Please Use AI" (791) pushed back on the fatigue, and Wozniak got cheered for telling graduates the AI that matters is "actual intelligence" (650).

So the net mood: skeptical and a bit exhausted, fascinated by agents precisely when they fail, increasingly focused on the legal and educational fallout, and rooting hard for open source — with a minority pushing back that the tools are genuinely useful if you slow down and use them well.

Want me to drill into the comments on any of these? The "I'm Tired of Talking to AI" thread and the "AI is slowing down" one are probably the richest for gauging sentiment.