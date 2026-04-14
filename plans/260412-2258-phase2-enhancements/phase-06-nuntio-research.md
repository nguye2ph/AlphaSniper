# Phase 6: Nuntio Discord Server Research

## Context Links

- [Brainstorm — Part 2C](../reports/brainstorm-260412-2258-ui-upgrade-discord.md)
- [Phase 4: Discord Bot](./phase-04-discord-bot.md)

## Overview

- **Priority**: P3
- **Status**: pending
- **Effort**: 1h
- **Description**: Research whether Nuntio Discord server allows bots. Document findings and plan integration or alternatives.

## Key Insights

- Nuntio is a paid financial news Discord server
- Most paid servers block user bots to protect content
- Need to check: server rules, ToS, bot policy
- If allowed: Phase 4 bot can join Nuntio as additional source
- If blocked: need alternative approaches (manual curation, webhooks, etc.)

## Requirements

### Functional
- Determine if bots are allowed in Nuntio server
- Document server rules and bot policy
- If allowed: document required permissions and channel structure
- If blocked: document alternatives

### Non-Functional
- Research only — no code changes
- Document findings for future reference

## Implementation Steps

### Step 1: Check Nuntio Server Rules (20min)

1. Join Nuntio Discord server (if not already member)
2. Read #rules or #info channel for bot policy
3. Check server settings → does it have bot verification level?
4. Look for existing bots in member list
5. Check if server uses anti-bot measures (verification, captcha)

### Step 2: Check Nuntio ToS (15min)

1. Review Nuntio website for Terms of Service
2. Look for API/data usage restrictions
3. Check if automated collection violates ToS
4. Look for official API or data export options

### Step 3: Test Bot Access (if allowed) (15min)

1. Try inviting Phase 4 bot to Nuntio server
2. If invite works: verify bot can read target channels
3. Test message reading capability
4. Check rate limits or restrictions

### Step 4: Document Findings (10min)

Create report: `plans/260412-2258-phase2-enhancements/reports/nuntio-research-findings.md`

Document:
- Server bot policy
- ToS restrictions
- Whether bot access is feasible
- Alternative approaches if blocked:
  - Manual copy-paste to own server → bot picks up from there
  - Nuntio API (if exists)
  - Browser extension to forward messages
  - Nuntio email alerts → email parser

## Todo List

- [ ] Check Nuntio server rules for bot policy
- [ ] Review Nuntio ToS for data usage restrictions
- [ ] Test bot invite (if rules allow)
- [ ] Document findings in report
- [ ] If allowed: add Nuntio channel IDs to Phase 4 config
- [ ] If blocked: document alternatives

## Test Cases

N/A — research phase, no code.

## Verification Steps

1. Findings documented in report
2. Decision recorded: proceed with bot or use alternative
3. If proceeding: channel IDs identified

## Acceptance Criteria

- [ ] Nuntio bot policy documented
- [ ] Clear yes/no answer on bot feasibility
- [ ] If no: at least one alternative approach documented
- [ ] Report filed in plans reports directory

## Success Criteria

- Clear decision on Nuntio integration path
- Actionable next steps documented

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Nuntio bans account for bot | High — lose subscription | Check rules first, don't test without permission |
| ToS violation | Medium — legal risk | Review ToS carefully before any automation |
| Server structure changes | Low — channels rename/move | Document current structure, monitor changes |

## Security Considerations

- Don't violate Nuntio ToS or server rules
- Don't redistribute Nuntio content publicly
- Bot should only collect for personal use

## Next Steps

- If allowed: update Phase 4 config with Nuntio channel IDs
- If blocked: implement manual curation workflow
- Future: explore Nuntio official API if one becomes available
