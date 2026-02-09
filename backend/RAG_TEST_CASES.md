# RAG Baseline Test Cases

Use these paragraphs in the Writer text box, then press **Tab** (last 1000 chars are sent). Check the **raw semantic scores** box and record the scores for each test paragraph and its prev/next.

All source files are from `data/raw_xml` and are **not** in the Final Dataset (used for baseline testing only).

---

## Upper Tribunal / EAT  -  Concurring

**File:** `Commerzbank AG v J Rajput.xml`  
**Opinion Type:** concurring  

### Test Case 1: Beginning Paragraph

**Test paragraph to paste:**

```
Ms S Clarke of Counsel(instructed by Aly & Hulme Associates) for the Respondent
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
Judgment approved by the courtCommerzbank AG v Ms J Rajput
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
The ET refused to direct that there be a preliminary hearing to determine whether a remitted tribunal hearing (due to commence next week) was bound by the factual findings of the original tribunal. The respondent appealed.
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 2: Middle Paragraph

**Test paragraph to paste:**

```
However, far from that prompting decisions on these matters of fundamental importance, the judge sent a decision to the parties on 8th September 2021 refusing the respondent’s application for a preliminary hearing.  This time the judge’s reasoning was that this was a matter for the fulltribunal, i.e. with judge and lay members, and that it would not be appropriate for him to deal with the matter in advance, sitting alone:
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
17.
	  
	    However, far from that prompting decisions on these matters of fundamental importance, the judge sent a decision to the parties on 8th September 2021 refusing the respondent’s application for a preliminary hearing.  This time the judge’s reasoning was that this was a matter for the fulltribunal, i.e. with judge and lay members, and that it would not be appropriate for him to deal with the matter in advance, sitting alone:  
	    
		
		  “25.
		  
		    The order sought at paragraph 14 envisages that I make a ruling, by myself, as a process of case management, on what findings of fact contained in the Tayler judgment, as remitted, are binding on a tribunal which hears that remitted claim. Such a ruling would fundamentally affect the rights of both parties to rely on findings of fact. It is common ground that at least some of the findings of fact are binding. To the extent that there is a dispute, it concerns which findings of fact are binding, and which are not.
		  
		
		
		  26.
		  
		    To resolve what facts remain binding, it is necessary, first, to finally determine what matters have been remitted. Whilst I have sought, at some length, to assist the parties with this, and whilst I have set out my understanding, that provisional ruling remains subject to any submissions by the parties. The determination of the scope of remission is for the tribunal that hears the remitted claim. It is for that tribunal, as a tribunal, to determine what claims have been remitted. When that process has been undertaken, it will be necessary for the tribunal to understand, having regard to the reason for remission, what effect it has, if any, on all or any of the findings of fact of the Tayler tribunal. Put simply, the tribunal that hears the remitted claim must decide which of the findings of fact are disturbed, and which are not.
		  
		
		
		  27.
		  
		    It is possible that all of the findings of fact remain binding. I have previously noted that the remission appears to revolve around matters treated as facts by the Tayler tribunal, but for which there was no evidence, or at least there was a failure to properly identify the contention that stereotypes exist and put the contention to any witness. It appears the EAT found that the Tayler tribunal either directly relied on those erroneous facts or drew impermissible secondary inferences. However, none of that, necessarily, undermines the findings of fact made by the Tayler Tribunal legitimately based on the evidence presented.
		  
		
		
		  
		    …
		  
		
		
		  30.
		  
		    I have considered whether determining what facts are binding could be some form of the preliminary issue. I find that preliminary issues can incorporate matters of evidence and findings of fact. For example, there may be a dispute as to whether certain evidence is admissible. It may be appropriate for a ruling on admissibility to be made prior to a hearing. The effect may be, ultimately, to determine the claim. That would be a preliminary issue.
		  
		
		
		  31.
		  
		    Specific discrete facts are often found by way preliminary issue, for example, the date of dismissal. Whilst those facts may be disputed, they can be resolved at a preliminary hearing, by way of a preliminary issue, by a judge sitting alone. However, the more ingrained the disputed facts are with the issues in the case, the less suitable is the matter for resolution as a preliminary issue. In this case, what facts remain binding at the remitted hearing cannot be excised, as some form of preliminary issue, from the main determination of the claim. What facts remain binding is fundamental to the resolution of this claim and should not be dealt with as a preliminary issue.
		  
		
		
		  32.
		  
		    It follows from what I have said that the order sought at paragraph 14 of the application is not one which can be determined as a matter of case management, and it is not one which should be determined as a preliminary issue. It must be determined by the final tribunal.”
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
“25.
		  
		    The order sought at paragraph 14 envisages that I make a ruling, by myself, as a process of case management, on what findings of fact contained in the Tayler judgment, as remitted, are binding on a tribunal which hears that remitted claim. Such a ruling would fundamentally affect the rights of both parties to rely on findings of fact. It is common ground that at least some of the findings of fact are binding. To the extent that there is a dispute, it concerns which findings of fact are binding, and which are not.
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 3: End Paragraph

**Test paragraph to paste:**

```
27.
	  
	    I was referred to various authorities by Mr Craig.  These include ILEA v Gravett [1988] IRLR 497, Heritage Homecare Ltd v Mason UKEAT/0273/14 and Elliott v Dorset CountyCouncil [2021] IRLR 880.  Whilst passages in those judgments to which my attention was drawn support the submission that, in those cases, a direction that there be a fresh hearing meant starting the hearing from scratch, I do not consider that any general rule can be laid down that, whenever the term “fresh hearings” is used, it must have that effect.  Each case will depend on its own facts and on the specific terms of the EAT’s judgment.  But, as I have said, in this case the terms of the judgment and the order are clear that the direction that there be a fresh re-hearing meant that the tribunal hearing the remitted matter would have to start from scratch.
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
I agree with the submissions made by Mr Craig and Mr Waseem (who appear for the respondent), that a fresh hearing (if directed) will, generally, mean just that; a hearing that considers the matters afresh with no limitation imposed by the findings of the previous tribunal.  I emphasise the word “generally” because that will not always be the case: there can be instances in which a fresh hearing could be directed in respect of a certain aspect of a claim, or in respect of a limited number of issues relatingto that claim.  However, if that is the case, the terms of the order and/or the judgment would, ordinarily, make that clear.  There is no such limitation here and, in fact, the terms of the judgment to which I have just referred make it clear that the stereotypical assumptions aspect of the decision is not something that can simply be hived off for another judge to determine, relying on the facts (or the primary facts) found by the Tayler Tribunal.
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
I was referred to various authorities by Mr Craig.  These include ILEA v Gravett [1988] IRLR 497, Heritage Homecare Ltd v Mason UKEAT/0273/14 and Elliott v Dorset CountyCouncil [2021] IRLR 880.  Whilst passages in those judgments to which my attention was drawn support the submission that, in those cases, a direction that there be a fresh hearing meant starting the hearing from scratch, I do not consider that any general rule can be laid down that, whenever the term “fresh hearings” is used, it must have that effect.  Each case will depend on its own facts and on the specific terms of the EAT’s judgment.  But, as I have said, in this case the terms of the judgment and the order are clear that the direction that there be a fresh re-hearing meant that the tribunal hearing the remitted matter would have to start from scratch.
```
**Next paragraph semantic score:** `[fill after testing]`

---

## Upper Tribunal / EAT  -  Dissenting

**File:** `Declan Durey v South Central Ambulance Service NHS Foundation Trust.xml`  
**Opinion Type:** dissenting  

### Test Case 1: Beginning Paragraph

**Test paragraph to paste:**

```
SOUTH CENTRAL AMBULANCE SERVICE NHS FOUNDATION TRUST
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
Judgment approved by the courtDurey v South Central Ambulance Service
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
Michael Avient (instructed by direct public access) for the Appellant
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 2: Middle Paragraph

**Test paragraph to paste:**

```
154.
		  
		    The Tribunal is satisfied that in respect of the claimant’s assertion that “an audit of a 999-call revealed that the call handler did not manage the clinical situation safely to reach a safe and appropriate outcome” the claimant made a disclosure of facts that in the reasonable belief of the claimant tended to show that the health or safety of service users of the respondent had been or was being endangered. We are satisfied that such a disclosure was in the public interest.”
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
Disclosure 9: The claimant contends that on the 25 September 2018 he informed Ms Jann about a number of matters during her investigation. The claimant relies on a list of seventeen acts or omissions by the respondent in the way it had dealt with the investigation into events around the matters giving rise to the disciplinary proceedings against Colleague X. The claimant states that these matters tended to show that the health or safety of service users of the respondent had been or was being endangered.
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
The Tribunal is satisfied that in respect of the claimant’s assertion that “an audit of a 999-call revealed that the call handler did not manage the clinical situation safely to reach a safe and appropriate outcome” the claimant made a disclosure of facts that in the reasonable belief of the claimant tended to show that the health or safety of service users of the respondent had been or was being endangered. We are satisfied that such a disclosure was in the public interest.”
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 3: End Paragraph

**Test paragraph to paste:**

```
These two strands of this ground face the following difficulties.  First, as to (a) the tribunal made a finding, in terms, at [167] that Mrs Gregory’s intention was to be supportive.  The respondent’s case was that, in light of the claimant, in his reply to her initial email, expressing concerns about how colleagues had been treating him, she felt that a meeting, rather than more emails, was needed; and it was her usual practice to relieve such an employee of their duties in order to facilitate such a meeting.  The tribunal heard Mrs Gregory give evidence, and it was entitled to accept the respondent’s case as to her motivation.  The high hurdle for a perversity challenge described by Mummery LJ in Yeboah v Crofton [2002] EWCA Civ 794; [2002] IRLR 634 is not surpassed.
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
73.
	  
	    These two strands of this ground face the following difficulties.  First, as to (a) the tribunal made a finding, in terms, at [167] that Mrs Gregory’s intention was to be supportive.  The respondent’s case was that, in light of the claimant, in his reply to her initial email, expressing concerns about how colleagues had been treating him, she felt that a meeting, rather than more emails, was needed; and it was her usual practice to relieve such an employee of their duties in order to facilitate such a meeting.  The tribunal heard Mrs Gregory give evidence, and it was entitled to accept the respondent’s case as to her motivation.  The high hurdle for a perversity challenge described by Mummery LJ in Yeboah v Crofton [2002] EWCA Civ 794; [2002] IRLR 634 is not surpassed.
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
74.
	  
	    In relation to Ms Saunders, as framed in the list of issues, the complaint was that she failed to prevent a recurrence of the conduct of which the claimant had complained in his grievance of 4 December 2018, when, by an email of 13 December, Mrs Gregory reiterated her intention to stand him down from his duties in order to meet her.  However, it appears that the emails showed that Mrs Gregory had first proposed to meet in early December, but later put forward revised dates, and, specifically, proposed 13 December in an email of 10 December.  The claimant then complained of that to Ms Saunders.  She then emailed him on 12 December informing him that Mrs Gregory would not be involved in line managing him until the grievance was resolved, and also asked him to provide suitable dates for a meeting with Ludlow Johnson (who was to investigate the grievance).  It was the respondent’s case that when, on 10 December, Mrs Gregory had emailed the claimant suggesting 13 December as a revised date for their meeting, she had not yet been told of the grievance.
```
**Next paragraph semantic score:** `[fill after testing]`

---

## Upper Tribunal / EAT  -  Majority

**File:** `Abraham Goldstein v MariePierre Herve.xml`  
**Opinion Type:** majority  

### Test Case 1: Beginning Paragraph

**Test paragraph to paste:**

```
Michael Salter (instructed by Fox & Partners Solicitors LLP) for the Appellant
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
Judgment Approved by the Court for handing down:GOLDSTEIN v HERVE AND ANOR
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
Louise Mankau (instructed by Rahman Lowe Solicitors) for the First Respondent
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 2: Middle Paragraph

**Test paragraph to paste:**

```
21.
	  
	    At this time, the respondent did not pay the wages, notice and holiday pay due to the claimant; only paying those sums shortly before the ET hearing.  The respondent told the ET he had felt the claimant had wronged him by walking off, and that the things she said in her resignation email were hostile towards him.
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
I expect you to cooperate fully and in good faith in an orderly handover process. This includes providing all information requested which is required for someone else to take over your work streams It would also include making yourself available by telephone for a certain period of time to answer questions that might arise and to which only you might know the answers. …”
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
At this time, the respondent did not pay the wages, notice and holiday pay due to the claimant; only paying those sums shortly before the ET hearing.  The respondent told the ET he had felt the claimant had wronged him by walking off, and that the things she said in her resignation email were hostile towards him.
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 3: End Paragraph

**Test paragraph to paste:**

```
(d)
	    
	      in circumstances of danger which the employee reasonably believed to be serious and imminent and which he could not reasonably have been expected to avert, he left (or proposed to leave) or (whilst the danger persisted) refused to return to his place of work or any dangerous part of his place of work, or
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
being an employee at a place where— (i) there was no such [health and safety] representative or safety committee, or (ii) there was such a representative or safety committee but it was not reasonably practicable for the employee to raise the matter by those means, he brought to his employer’s attention, by reasonable means, circumstances connected with his work which he reasonably believed were harmful or potentially harmful to health or safety,
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
in circumstances of danger which the employee reasonably believed to be serious and imminent and which he could not reasonably have been expected to avert, he left (or proposed to leave) or (whilst the danger persisted) refused to return to his place of work or any dangerous part of his place of work, or
```
**Next paragraph semantic score:** `[fill after testing]`

---

## UK Supreme Court  -  Concurring

**File:** `Antony Savva v Leather Inside Out in liquidation  Ors.xml`  
**Opinion Type:** concurring  

### Test Case 1: Beginning Paragraph

**Test paragraph to paste:**

```
The First Respondent did not appear and was not represented
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
Judgment approved by the court for handing downSavva v Leather Inside Out (in liquidation), others
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
Joel Wallace (instructed by Forsters) for the Second and Fourth Respondents
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 2: Middle Paragraph

**Test paragraph to paste:**

```
55.
	  
	    At [35] Mummery LJ said:
	    
		
		  
		    “In order to determine whether the acts are part of a series some evidence is needed to determine what link, if any, there is between the acts in the 3 month period and the acts outside the 3 month period. We know that they are alleged to have been committed against Mr Arthur. That by itself would hardly make them part of a series or similar. It is necessary to look at all the circumstances surrounding the acts. Were they all committed by fellow employees? If not, what connection, if any, was there between the alleged perpetrators? Were their actions organised or concerted in some way? It would also be relevant to inquire why they did what is alleged. I do not find "motive" a helpful departure from the legislative language according to which the determining factor is whether the act was done "on the ground" that the employee had made a protected disclosure. Depending on the facts I would not rule out the possibility of a series of apparently disparate acts being shown to be part of a series or to be similar to one another in a relevant way by reason of them all being on the ground of a protected disclosure.”
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
“The acts occurring in the 3 month period may not be isolated one-off acts, but connected to earlier acts or failures outside the period. It may not be possible to characterise it as a case of an act extending over a period within section 48(4) by reference, for example, to a connecting rule, practice, scheme or policy but there may be some link between them which makes it just and reasonable for them to be treated as in time and for the complainant to be able to rely on them. Section 48(3) is designed to cover such a case. There must be some relevant connection between the acts in the 3 month period and those outside it. The necessary connections were correctly identified by HHJ Reid as (a) being part of a "series" and (b) being acts which are "similar" to one another.”
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
“In order to determine whether the acts are part of a series some evidence is needed to determine what link, if any, there is between the acts in the 3 month period and the acts outside the 3 month period. We know that they are alleged to have been committed against Mr Arthur. That by itself would hardly make them part of a series or similar. It is necessary to look at all the circumstances surrounding the acts. Were they all committed by fellow employees? If not, what connection, if any, was there between the alleged perpetrators? Were their actions organised or concerted in some way? It would also be relevant to inquire why they did what is alleged. I do not find "motive" a helpful departure from the legislative language according to which the determining factor is whether the act was done "on the ground" that the employee had made a protected disclosure. Depending on the facts I would not rule out the possibility of a series of apparently disparate acts being shown to be part of a series or to be similar to one another in a relevant way by reason of them all being on the ground of a protected disclosure.”
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 3: End Paragraph

**Test paragraph to paste:**

```
Ground (a) complains that the tribunal erred because it failed to determine the claimant’s complaint that the failure to respond at all to the third SAR (raised in May 2022) amounted to detrimental treatment on grounds of protected disclosures.  As I have recorded, the claimant was permitted to add that complaint, by amendment, in the Beyzade reconsideration decision.  However, the Gidney tribunal did not address it in their decision.  The claimant raised this omission in his reconsideration application, but the Gidney reconsideration decision also failed to address it.  I conclude that the Gidney tribunal did err by failing to determine this complaint, an error which was not remedied upon reconsideration.  I therefore uphold this ground.
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
93.
	  
	    Ground (a) complains that the tribunal erred because it failed to determine the claimant’s complaint that the failure to respond at all to the third SAR (raised in May 2022) amounted to detrimental treatment on grounds of protected disclosures.  As I have recorded, the claimant was permitted to add that complaint, by amendment, in the Beyzade reconsideration decision.  However, the Gidney tribunal did not address it in their decision.  The claimant raised this omission in his reconsideration application, but the Gidney reconsideration decision also failed to address it.  I conclude that the Gidney tribunal did err by failing to determine this complaint, an error which was not remedied upon reconsideration.  I therefore uphold this ground.
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
94.
	  
	    Ground (b) contends that the tribunal misapplied schedule 2 part 1 paragraph 2 Data Protection Act 2018 by accepting the charity’s reliance, in declining to comply with the first two SARs, on an exemption “that did not legally apply”.
```
**Next paragraph semantic score:** `[fill after testing]`

---

## UK Supreme Court  -  Dissenting

**File:** `A Reference by the Attorney General for Northern Ireland of devolution issues to the Supreme Court pursuant to Paragraph 34 of Schedule 10 to the Northern Ireland Act 1998 Northern Ireland.xml`  
**Opinion Type:** dissenting  

### Test Case 1: Beginning Paragraph

**Test paragraph to paste:**

```
(Instructed by Office of the Attorney General for Northern Ireland)
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
A Reference by the Attorney General for Northern Ireland of devolution issues to the Supreme Court pursuant to Paragraph 34 of Schedule 10 to the Northern Ireland Act 1998 (Northern Ireland)
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
(Instructed by Departmental Solicitor’s Office, Department of Finance and Personnel)
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 2: Middle Paragraph

**Test paragraph to paste:**

```
6.
	  
	    Acts by the Secretary of State or by departments in Westminster do not come within the purview of section 24 of the 1998 Act. In order for a devolution issue to arise, therefore, it must be shown that an act has been carried out or a function has been discharged by a Northern Ireland Minister or a Northern Ireland department.
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
The Attorney General submits that a devolution issue arises because the provision of lists by the Department for Communities is necessary in order to give effect to the Secretary of State’s commencement orders. The Department refutes this, contending that its role in issuing the relevant lists amounts to nothing more than providing administrative support to the Secretary of State. The commencement orders define the relevant territories by reference to lists of postcodes issued by the Department. The lists were not prepared, however, pursuant to any statutory or other power and do not have any independent legal force or effect, the Department says. They are incorporated by reference into the commencement orders and therefore have legal effects solely by reason of the act of the Secretary of State, not the act of the Department.
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
Acts by the Secretary of State or by departments in Westminster do not come within the purview of section 24 of the 1998 Act. In order for a devolution issue to arise, therefore, it must be shown that an act has been carried out or a function has been discharged by a Northern Ireland Minister or a Northern Ireland department.
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 3: End Paragraph

**Test paragraph to paste:**

```
The contrary view is that the provision of postcodes was indispensable to the effective introduction of the welfare reforms. Without them, the commencement orders could not operate. Conceivably, they could have been compiled by a Westminster department which would have rendered the act of preparing the lists immune from challenge as a devolution issue. But, in fact, they were not. A Northern Ireland department prepared the lists. Their existence was integral to the operation of the welfare reforms. The act of preparing the lists and providing them to the Secretary of State constituted an act for the purpose of section 24 of the 1998 Act.
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
10.
	  
	    The contrary view is that the provision of postcodes was indispensable to the effective introduction of the welfare reforms. Without them, the commencement orders could not operate. Conceivably, they could have been compiled by a Westminster department which would have rendered the act of preparing the lists immune from challenge as a devolution issue. But, in fact, they were not. A Northern Ireland department prepared the lists. Their existence was integral to the operation of the welfare reforms. The act of preparing the lists and providing them to the Secretary of State constituted an act for the purpose of section 24 of the 1998 Act.
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
11.
	  
	    It is, I believe, important to recognise that the distinct prohibitions in section 24 are disjunctive. Thus, it is forbidden to make, confirm or approve any subordinate legislation, orto do any act, so far as the legislation or act is incompatible with any of the Convention rights. The section comprehends, therefore, not only the enactment of subordinate legislation but also acts which may be ancillary or even incidental to that enactment. On a theoretical or technical level, therefore, the compiling of lists of postcodes and providing them as a means of facilitating the introduction of the commencement orders is an act or the discharge of a function under paragraph 1(b) of Schedule 10 to the 1998 Act.
```
**Next paragraph semantic score:** `[fill after testing]`

---

## UK Supreme Court  -  Majority

**File:** `AEL v Flight Centre UK Ltd.xml`  
**Opinion Type:** majority  

### Test Case 1: Beginning Paragraph

**Test paragraph to paste:**

```
The Respondent, did not appear and was not represented
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
Judgment approved by the court for a hand downAEL v Flight Centre (UK) Ltd
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
The Employment Tribunal erred in failing to consider the application for reconsideration of the correct application for anonymity which the Appellant had made. The Appellant had made two relevant applications for anonymity – the first, dated 14 July 2021, was rejected by the Tribunal in a judgment dated 26 July 2021. The Appellant then made a further application on 4 August 2021 supported by a disability impact statement and medical records. That application was considered by the ET on 9 September 2021, by which point the Appellants claims against her former employer had been compromised. The 4 August 2021 application was rejected by the Tribunal under the terms of a decision issued on 9 September 2021. The Appellant applied for reconsideration of that decision on 17 September 2021. However, when that application was considered by the Tribunal under the terms of a decision issued on 21 March 2022, it was treated not as an application in respect of the decision issued on 9 September 2021 but as one made by reference to the earlier decision of 26 July 2021. To that extent therefore, it appeared that the ET had fallen into error
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 2: Middle Paragraph

**Test paragraph to paste:**

```
-
	    
	      X v Y UKEAT/0302/18/RN – A rule 50 order can be made at any time, even where proceedings are substantially over. There may be good reasons for anonymisation under Rule 50 bearing in mind an individual’s Article 8 rights;
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
The response on behalf of the Attorney General came in a letter of 18 October 2023. The decision was made that the test for appointing an advocate to the appeal had not been met in that given the case law currently available relating to the making of anonymity order, there was “not a significant risk of an important and difficult point of law being determined without the court or tribunal hearing all relevant arguments.” The letter identified and summarised the key cases in this area as follows:
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
X v Y UKEAT/0302/18/RN – A rule 50 order can be made at any time, even where proceedings are substantially over. There may be good reasons for anonymisation under Rule 50 bearing in mind an individual’s Article 8 rights;
```
**Next paragraph semantic score:** `[fill after testing]`

---

### Test Case 3: End Paragraph

**Test paragraph to paste:**

```
a “case management order”, or decision of any kind in relation to the conduct of proceedings, not including the determination of any issue which would be the subject of a judgement; or
```
**Semantic score (predictions):** Run RAG (Tab) and record the raw similarity value from the right-pane box.  
**Expected semantic score:** `[fill after testing]`

**Previous paragraph:**

```
(a)
	      
		a “case management order”, or decision of any kind in relation to the conduct of proceedings, not including the determination of any issue which would be the subject of a judgement; or
```
**Previous paragraph semantic score:** `[fill after testing]`

**Next paragraph:**

```
(b)
	      
		a “judgment”, decision, made at any stage of the proceedings (but not including a decision under rule 13 or 19), which finally determines:
	      
	      
		(i)
		
		  a claim or part of a claim, as regards liability, remedy or costs (including preparation time and wasted costs);
		
	      
	      
		(ii)
		
		  any issue which is capable of finally disposing of any claim, or part of a claim, even if it does not necessarily do so (for example, an issue whether a claim should be struck out or a jurisdictional issue);
		
	      
	      
		(iii)
		
		  the imposition of a financial penalty under section 12A of the Employment Tribunals Act.”
```
**Next paragraph semantic score:** `[fill after testing]`

---

