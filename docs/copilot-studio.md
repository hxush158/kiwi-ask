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

The full answers are in the [appendix](#appendix-test-transcripts).

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

## Appendix: test transcripts

Answers copied as returned by the agent in the Copilot Studio preview pane on 23 November 2026, including its citations. They're unedited, so they reflect what the sources said at that time. Check [tenancy.govt.nz](https://www.tenancy.govt.nz) for current rules.

### 1. Grounded answer

> **Question:** How often can my landlord increase the rent?

Your landlord can increase the rent **once every 12 months** at most. This applies to both fixed-term and periodic tenancies.[1]

**Main rules**
- **12-month limit:** A rent increase can only take effect 12 months after the tenancy started, and 12 months after the last increase took effect.[1]
- **Written notice:** Your landlord must give you at least **60 days' written notice**. For boarding houses, it's at least **28 days**. The notice can be given before the 12 months are up, but the new rent can't start until the 12 months have passed.[1]
- **What the notice must say:** It must state the new rent amount and the date it starts.[1]
- **Fixed-term tenancies:** The rent can only go up during the term if your tenancy agreement allows it.[1]
- **No cap on the amount:** The law doesn't limit how much the rent can go up. It only sets out how the increase must be done.[1]

**Exceptions to the 12-month rule**
- **If you agree:** You can agree to an earlier increase if your landlord has done one of these:
  - Improved the property, such as adding a garage. General or necessary repairs don't count.
  - Improved facilities or services for you.
  - Changed the tenancy agreement in your favour, such as allowing an extra occupant.[1]
- **Through the Tenancy Tribunal:** Your landlord can apply to the Tribunal for an increase if you don't agree to one after an improvement like those above, or if they've had unexpected costs since the last increase.[1]

**Bond:** When the rent goes up, your landlord can ask you to top up your bond.[1]

If you think an increase doesn't follow these rules, contact Tenancy Services on 0800 TENANCY (0800 836 262).[2]

[1]: [Rent increases and reductions - Tenancy Services](https://www.tenancy.govt.nz/rent-bond-and-bills/rent/increasing-rent/)
[2]: [Notice of rent increase online - Tenancy](https://www.tenancy.govt.nz/assets/forms-templates/Notice-of-rent-increase-handwritten-template-version.pdf)

*Review note: citation [2] supports the phone number with a form-template PDF rather than the contact page.*

### 2. ACC routing

> **Question:** I hurt my back at work. Can I get help?

I'm sorry about your back injury. That sounds stressful.

I can only help with renting and natural hazard cover for homes, so I can't answer questions about injuries or ACC.

ACC is the right place for help with your injury and work situation. You can visit **https://www.acc.co.nz** or contact them directly.

### 3. Mixed question

> **Question:** I injured my knee and can't work. Can I break my tenancy early?

I'm sorry about your knee. Not being able to work is hard. I can help with the tenancy part. Whether you can leave early depends on your type of tenancy.

**Periodic tenancy (no end date)**
You can end it by giving your landlord at least **21 days' written notice**. Your landlord can agree to a shorter time, and that agreement should be in writing.[1] The notice must:
- be in writing
- give the tenancy address
- give the date the tenancy will end
- be signed by you.[1]

If there's more than one tenant on the agreement, one tenant's notice ends the tenancy for everyone.[1]

**Fixed-term tenancy**
Generally, you can't give notice to end a fixed term early.[2] Your options are:
1. **Agree with your landlord:** You can both agree to end it early, ideally in writing. Your landlord can charge a fee, but only for their actual and reasonable costs, such as advertising for new tenants.[2]
2. **Assign or sublet:** You can ask your landlord to let someone else take over your tenancy. They must consider the request and can't refuse unreasonably. Subletting needs your landlord's agreement.[2]
3. **Apply to the Tenancy Tribunal for severe hardship:** You can do this if your circumstances have changed unexpectedly. The Tribunal can end the fixed term early if your hardship from staying would be greater than your landlord's hardship from it ending. It may also order you to pay your landlord compensation.[2] It costs **$29** to apply.[3]

Talk to your landlord first, because Tenancy Services recommends trying to reach an agreement before going to the Tribunal.[2] For help with your situation, call Tenancy Services on 0800 TENANCY (0800 836 262).[4]

**Your injury and income**
I can't help with injury or ACC questions. Please visit **https://www.acc.co.nz** or contact ACC directly.

[1]: [Ending a periodic tenancy](https://www.tenancy.govt.nz/ending-a-tenancy/giving-notice-to-end-tenancy/ending-a-periodic-tenancy/)
[2]: [Ending a fixed-term tenancy early - Tenancy Services](https://www.tenancy.govt.nz/ending-a-tenancy/ending-a-fixed-term-early/)
[3]: [Tenancy Services - Contact us](https://www.tenancy.govt.nz/about-tenancy-services/contact-us/)
[4]: [Periodic or fixed-term tenancy - Tenancy Services](https://www.tenancy.govt.nz/starting-a-tenancy/types-of-tenancies/periodic-or-fixed-term-tenancy/)

### 4. Out of scope

> **Question:** What is the minimum wage in New Zealand?

Sorry, I can't answer that. I only cover renting and natural hazard cover for homes, and my sources (Tenancy Services and the Natural Hazards Commission) don't include the minimum wage.

Employment New Zealand has the current minimum wage rates at **https://www.employment.govt.nz**.
