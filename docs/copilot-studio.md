# KiwiAsk Home Helper – Copilot Studio agent

A low-code companion to KiwiAsk, built on 23 November 2026 to get hands-on with Microsoft Copilot Studio. It answers questions about renting and natural hazard cover in New Zealand, grounded only in official sources.

**Outcome:** the agent was built, configured and tested; 4 of 4 test scenarios passed.

## What the agent does

- **Instructions:** answer only from the knowledge sources and cite the source page; if the sources don't cover a question, say so and point to the relevant official website; route injury and ACC questions to ACC; don't give legal advice.
- **Knowledge:** `tenancy.govt.nz` and `naturalhazards.govt.nz` only. The default "Search all websites" source was removed so the agent can't fall back to the open web.
- **ACC handled by routing, not as a knowledge source.** ACC's terms of use don't allow its content to be republished or stored for third-party access, so the agent directs users to acc.co.nz instead. This matches the data-licensing decision for KiwiAsk M1 (see [specs](specs/)).
- **Tools:** the default Work IQ tool (Microsoft 365 work data) was removed because the agent doesn't need it.

## Test results

| Scenario | Question | Result |
| --- | --- | --- |
| Grounded answer | How often can my landlord increase the rent? | ✅ Correct (once every 12 months), with tenancy.govt.nz citations |
| ACC routing | I hurt my back at work. Can I get help? | ✅ Acknowledged the situation and routed to ACC |
| Mixed question | I injured my knee and can't work. Can I break my tenancy early? | ✅ Answered the tenancy part with citations; routed only the injury part to ACC |
| Out of scope | What is the minimum wage in New Zealand? | ✅ Declined and pointed to Employment New Zealand |

**Why the first test matters:** in the M0 experiments ([ai-workflow.md](ai-workflow.md)), the ungrounded model got this same rent-increase rule wrong at every reasoning level. Grounded in the official source, the agent answers it correctly. This is the same evidence that motivates the RAG design in M1.

**Review note:** in the first answer, the citation for the Tenancy Services phone number pointed to a form-template PDF rather than the contact page. The answer was still correct, but citation quality needs human review, not just answer accuracy.

## Setup: from a personal account to a working agent

Getting a trial agent running in a brand-new tenant took eight fixes. Each one is a tenant, licensing or permissions issue that a customer rollout could hit too.

| # | Blocker | Cause | Fix |
| --- | --- | --- | --- |
| 1 | Sign-up rejected | Copilot Studio doesn't accept personal Microsoft accounts | Created a work account in the Entra directory that came with my Azure subscription |
| 2 | "Dataverse isn't set up in this environment" | The tenant's default environment has no Dataverse | Needed a separate environment with Dataverse |
| 3 | No Environments menu in the Power Platform admin center | The new account had no admin role | Assigned the Power Platform Administrator role |
| 4 | "The user does not have a license that allows environment creation" | No Power Platform licence on the account | Signed up for the Power Apps Developer Plan, which created a developer environment with Dataverse |
| 5 | Agent and skill wouldn't save ("User license not found") | The account had Power Apps and Power Automate licences, but no Copilot Studio licence | Started the Copilot Studio trial through Microsoft's official sign-up link |
| 6 | Copilot Studio still showed the default environment | The environment switcher is at the bottom left in the new UI | Switched to the developer environment, and the agent saved |
| 7 | "This environment is out of credits" | The environment had 0 Copilot Credits | Moved to Azure pay-as-you-go billing |
| 8 | No Azure subscription available in the billing plan | The work account had no role on the subscription | Granted it Contributor on the subscription and registered the `Microsoft.PowerPlatform` resource provider; created a billing plan with only the Copilot Studio and Dataverse meters, billed to the KiwiAsk resource group |

**Docs vs reality:** Microsoft's documentation says pay-as-you-go is available for production and sandbox environments. The admin center still listed the developer environment, and linking it worked, so I didn't need to create a sandbox and rebuild the agent.

**A verification step that mattered:** before granting Contributor on the subscription, the member picker showed the work account under its contact email rather than its sign-in name. I searched by the sign-in name to confirm it was the right identity before assigning a role with that much access.

## Cost control

- Only two meters enabled: Copilot Studio and Dataverse.
- The subscription has a monthly budget alert.
- After testing, I removed the environment from the billing plan so no further usage is charged. I'll add it back when I need to test again.

## Limitations

- **Trial only.** The trial can't publish the agent to a channel; testing was done in the Copilot Studio preview pane.
- **Small test set.** Four scenarios check the key behaviours, but this isn't a full evaluation. A larger test set using Copilot Studio's Evaluate feature would be the next step.
- **Web knowledge, not an index.** The agent uses public websites as knowledge. KiwiAsk M1 builds its own Azure AI Search index from a curated document set, which gives more control over chunking, metadata and citations.
