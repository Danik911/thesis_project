# INTERNATIONAL ISO/IEC STANDARD 27001

# Information technology — Security techniques — Information security management systems — Requirements

# Technologies de l’information — Techniques de sécurité — Systèmes de management de la sécurité de l’information — Exigences

Reference number: ISO/IEC FDIS 27001:2013(E)

© ISO/IEC 2013
---
# ISO/IEC 27001:2013(E)

COPYRIGHT PROTECTED DOCUMENT

© ISO/IEC 2013

All rights reserved. Unless otherwise specified, no part of this publication may be reproduced or utilized otherwise in any form or by any means, electronic or mechanical, including photocopying, or posting on the internet or an intranet, without prior written permission. Permission can be requested from either ISO at the address below or ISO’s member body in the country of the requester.

ISO copyright office

Case postale 56 • CH-1211 Geneva 20

Tel. + 41 22 749 01 11

Fax + 41 22 749 09 47

E-mail copyright@iso.org

Web www.iso.org

Published in Switzerland

ii © ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Contents

| Foreword                                                                | iv |
| ----------------------------------------------------------------------- | -- |
| 0 Introduction                                                          | v  |
| 1 Scope                                                                 | 1  |
| 2 Normative references                                                  | 1  |
| 3 Terms and definitions                                                 | 1  |
| 4 Context of the organization                                           | 1  |
| 4.1 Understanding the organization and its context                      | 1  |
| 4.2 Understanding the needs and expectations of interested parties      | 1  |
| 4.3 Determining the scope of the information security management system | 1  |
| 4.4 Information security management system                              | 2  |
| 5 Leadership                                                            | 2  |
| 5.1 Leadership and commitment                                           | 2  |
| 5.2 Policy                                                              | 2  |
| 5.3 Organizational roles, responsibilities and authorities              | 3  |
| 6 Planning                                                              | 3  |
| 6.1 Actions to address risks and opportunities                          | 3  |
| 6.2 Information security objectives and plans to achieve them           | 5  |
| 7 Support                                                               | 5  |
| 7.1 Resources                                                           | 5  |
| 7.2 Competence                                                          | 5  |
| 7.3 Awareness                                                           | 5  |
| 7.4 Communication                                                       | 6  |
| 7.5 Documented information                                              | 6  |
| 8 Operation                                                             | 7  |
| 8.1 Operational planning and control                                    | 7  |
| 8.2 Information security risk assessment                                | 7  |
| 8.3 Information security risk treatment                                 | 7  |
| 9 Performance evaluation                                                | 7  |
| 9.1 Monitoring, measurement, analysis and evaluation                    | 7  |
| 9.2 Internal audit                                                      | 8  |
| 9.3 Management review                                                   | 8  |
| 10 Improvement                                                          | 9  |
| 10.1 Nonconformity and corrective action                                | 9  |
| 10.2 Continual improvement                                              | 9  |
| Annex A (normative) Reference control objectives and controls           | 10 |
| Bibliography                                                            | 23 |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Foreword

ISO (the International Organization for Standardization) and IEC (the International Electrotechnical Commission) form the specialized system for worldwide standardization. National bodies that are members of ISO or IEC participate in the development of International Standards through technical committees established by the respective organization to deal with particular fields of technical activity. ISO and IEC technical committees collaborate in fields of mutual interest. Other international organizations, governmental and non-governmental, in liaison with ISO and IEC, also take part in the work. In the field of information technology, ISO and IEC have established a joint technical committee, ISO/IEC JTC 1.

International Standards are drafted in accordance with the rules given in the ISO/IEC Directives, Part 2. The main task of the joint technical committee is to prepare International Standards. Draft International Standards adopted by the joint technical committee are circulated to national bodies for voting. Publication as an International Standard requires approval by at least 75 % of the national bodies casting a vote.

Attention is drawn to the possibility that some of the elements of this document may be the subject of patent rights. ISO and IEC shall not be held responsible for identifying any or all such patent rights.

ISO/IEC 27001 was prepared by Joint Technical Committee ISO/IEC JTC 1, Information technology, Subcommittee SC 27, IT Security techniques.

This second edition cancels and replaces the first edition (ISO/IEC 27001:2005), which has been technically revised.

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# 0 Introduction

# 0.1 General

This International Standard has been prepared to provide requirements for establishing, implementing,
maintaining and continually improving an information security management system. The adoption of an
information security management system is a strategic decision for an organization. The establishment
and implementation of an organization’s information security management system is influenced by the
organization’s needs and objectives, security requirements, the organizational processes used and the
size and structure of the organization. All of these influencing factors are expected to change over time.
The information security management system preserves the confidentiality, integrity and availability
of information by applying a risk management process and gives confidence to interested parties that
risks are adequately managed.

It is important that the information security management system is part of and integrated with the
organization’s processes and overall management structure and that information security is considered
in the design of processes, information systems, and controls. It is expected that an information security
management system implementation will be scaled in accordance with the needs of the organization.
This International Standard can be used by internal and external parties to assess the organization’s
ability to meet the organization’s own information security requirements.

The order in which requirements are presented in this International Standard does not reflect their
importance or imply the order in which they are to be implemented. The list items are enumerated for
reference purpose only.

ISO/IEC 27000 describes the overview and the vocabulary of information security management
systems, referencing the information security management system family of standards (including
ISO/IEC 27003[2], ISO/IEC 27004[3] and ISO/IEC 27005[4]), with related terms and definitions.

# 0.2 Compatibility with other management system standards

This International Standard applies the high level structure, identical sub clause titles, identical text,
common terms, and core definitions defined in Annex SL of ISO/IEC Directives, Part 1, Consolidated ISO
Supplement, and therefore maintains compatibility with other management system standards that have
adopted the Annex SL.

This common approach defined in the Annex SL will be useful for those organizations that choose to operate
a single management system that meets the requirements of two or more management system standards.

© ISO/IEC 2013 – All rights reserved
---
NO_CONTENT_HERE
---
# FINAL DRAFT INTERNATIONAL STANDARD

# ISO/IEC 27001:2013(E)

# Information technology — Security techniques —

# Information security management systems — Requirements

# 1 Scope

This International Standard specifies the requirements for establishing, implementing, maintaining and continually improving an information security management system within the context of the organization. This International Standard also includes requirements for the assessment and treatment of information security risks tailored to the needs of the organization. The requirements set out in this International Standard are generic and are intended to be applicable to all organizations, regardless of type, size or nature. Excluding any of the requirements specified in Clauses 4 to 10 is not acceptable when an organization claims conformity to this International Standard.

# 2 Normative references

The following documents, in whole or in part, are normatively referenced in this document and are indispensable for its application. For dated references, only the edition cited applies. For undated references, the latest edition of the referenced document (including any amendments) applies.

ISO/IEC 27000, Information technology — Security techniques — Information security management systems — Overview and vocabulary

# 3 Terms and definitions

For the purposes of this document, the terms and definitions given in ISO/IEC 27000 apply.

# 4 Context of the organization

# 4.1 Understanding the organization and its context

The organization shall determine external and internal issues that are relevant to its purpose and that affect its ability to achieve the intended outcome(s) of its information security management system.

NOTE Determining these issues refers to establishing the external and internal context of the organization considered in Clause 5.3 of ISO 31000:2009[5].

# 4.2 Understanding the needs and expectations of interested parties

The organization shall determine:

- a) interested parties that are relevant to the information security management system; and
- b) the requirements of these interested parties relevant to information security.

NOTE The requirements of interested parties may include legal and regulatory requirements and contractual obligations.

# 4.3 Determining the scope of the information security management system

The organization shall determine the boundaries and applicability of the information security management system to establish its scope.

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

When determining this scope, the organization shall consider:

- a) the external and internal issues referred to in 4.1;
- b) the requirements referred to in 4.2; and
- c) interfaces and dependencies between activities performed by the organization, and those that are performed by other organizations.

The scope shall be available as documented information.

# 4.4 Information security management system

The organization shall establish, implement, maintain and continually improve an information security management system, in accordance with the requirements of this International Standard.

# 5 Leadership

# 5.1 Leadership and commitment

Top management shall demonstrate leadership and commitment with respect to the information security management system by:

- a) ensuring the information security policy and the information security objectives are established and are compatible with the strategic direction of the organization;
- b) ensuring the integration of the information security management system requirements into the organization’s processes;
- c) ensuring that the resources needed for the information security management system are available;
- d) communicating the importance of effective information security management and of conforming to the information security management system requirements;
- e) ensuring that the information security management system achieves its intended outcome(s);
- f) directing and supporting persons to contribute to the effectiveness of the information security management system;
- g) promoting continual improvement; and
- h) supporting other relevant management roles to demonstrate their leadership as it applies to their areas of responsibility.

# 5.2 Policy

Top management shall establish an information security policy that:

- a) is appropriate to the purpose of the organization;
- b) includes information security objectives (see 6.2) or provides the framework for setting information security objectives;
- c) includes a commitment to satisfy applicable requirements related to information security; and
- d) includes a commitment to continual improvement of the information security management system.

The information security policy shall:

- e) be available as documented information;

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

f) be communicated within the organization; and

g) be available to interested parties, as appropriate.

# 5 Organizational roles, responsibilities and authorities

Top management shall ensure that the responsibilities and authorities for roles relevant to information security are assigned and communicated.

Top management shall assign the responsibility and authority for:

- a) ensuring that the information security management system conforms to the requirements of this International Standard; and
- b) reporting on the performance of the information security management system to top management.

NOTE Top management may also assign responsibilities and authorities for reporting performance of the information security management system within the organization.

# 6 Planning

# 6.1 Actions to address risks and opportunities

# 6.1.1 General

When planning for the information security management system, the organization shall consider the issues referred to in 4.1 and the requirements referred to in 4.2 and determine the risks and opportunities that need to be addressed to:

- a) ensure the information security management system can achieve its intended outcome(s);
- b) prevent, or reduce, undesired effects; and
- c) achieve continual improvement.

The organization shall plan:

- d) actions to address these risks and opportunities; and
- e) how to

# 6.1.2 Information security risk assessment

The organization shall define and apply an information security risk assessment process that:

- a) establishes and maintains information security risk criteria that include:
- - 1) the risk acceptance criteria; and
- 2) criteria for performing information security risk assessments;

b) ensures that repeated information security risk assessments produce consistent, valid and comparable results;

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# 6.1.2 Information security risk assessment

c) identifies the information security risks:

1. apply the information security risk assessment process to identify risks associated with the loss of confidentiality, integrity and availability for information within the scope of the information security management system; and
2. identify the risk owners;

d) analyses the information security risks:

1. assess the potential consequences that would result if the risks identified in 6.1.2 c) 1) were to materialize;
2. assess the realistic likelihood of the occurrence of the risks identified in 6.1.2 c) 1); and
3. determine the levels of risk;

e) evaluates the information security risks:

1. compare the results of risk analysis with the risk criteria established in 6.1.2 a); and
2. prioritize the analysed risks for risk treatment.

The organization shall retain documented information about the information security risk assessment process.

# 6.1.3 Information security risk treatment

The organization shall define and apply an information security risk treatment process to:

1. select appropriate information security risk treatment options, taking account of the risk assessment results;
2. determine all controls that are necessary to implement the information security risk treatment option(s) chosen;
3. NOTE Organizations can design controls as required, or identify them from any source.

compare the controls determined in 6.1.3 b) above with those in Annex A and verify that no necessary controls have been omitted;
4. NOTE 1 Annex A contains a comprehensive list of control objectives and controls. Users of this International Standard are directed to Annex A to ensure that no necessary controls are overlooked.

NOTE 2 Control objectives are implicitly included in the controls chosen. The control objectives and controls listed in Annex A are not exhaustive and additional control objectives and controls may be needed.

produce a Statement of Applicability that contains the necessary controls (see 6.1.3 b) and c)) and justification for inclusions, whether they are implemented or not, and the justification for exclusions of controls from Annex A;
5. formulate an information security risk treatment plan; and
6. obtain risk owners’ approval of the information security risk treatment plan and acceptance of the residual information security risks.

The organization shall retain documented information about the information security risk treatment process.

NOTE The information security risk assessment and treatment process in this International Standard aligns with the principles and generic guidelines provided in ISO 31000[5].

© ISO/IEC 2013 – All rights reserved
---
# 6.2   Information security objectives and plans to achieve them

The organization shall establish information security objectives at relevant functions and levels. The information security objectives shall:

- a)   be consistent with the information security policy;
- b)   be measurable (if practicable);
- c)   take into account applicable information security requirements, and risk assessment and risk treatment results;
- d)   be communicated; and
- e)   be updated as appropriate.

The organization shall retain documented information on the information security objectives.

When planning how to achieve its information security objectives, the organization shall determine:

- f)   what will be done;
- g)   what resources will be required;
- h)   who will be responsible;
- i)   when it will be completed; and
- j)   how the results will be evaluated.

# 7    Support

# 7.1   Resources

The organization shall determine and provide the resources needed for the establishment, implementation, maintenance and continual improvement of the information security management system.

# 7.2   Competence

The organization shall:

- a)   determine the necessary competence of person(s) doing work under its control that affects its information security performance;
- b)   ensure that these persons are competent on the basis of appropriate education, training, or experience;
- c)   where applicable, take actions to acquire the necessary competence, and evaluate the effectiveness of the actions taken; and
- d)   retain appropriate documented information as evidence of competence.

NOTE       Applicable actions may include, for example: the provision of training to, the mentoring of, or the re-assignment of current employees; or the hiring or contracting of competent persons.

# 7.3   Awareness

Persons doing work under the organization’s control shall be aware of:

- a)   the information security policy;

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

b) their contribution to the effectiveness of the information security management system, including the benefits of improved information security performance; and

c) the implications of not conforming with the information security management system requirements.

# 7.4 Communication

The organization shall determine the need for internal and external communications relevant to the information security management system including:

- a) on what to communicate;
- b) when to communicate;
- c) with whom to communicate;
- d) who shall communicate; and
- e) the processes by which communication shall be effected.

# 7.5 Documented information

# 7.5.1 General

The organization’s information security management system shall include:

- a) documented information required by this International Standard; and
- b) documented information determined by the organization as being necessary for the effectiveness of the information security management system.

NOTE The extent of documented information for an information security management system can differ from one organization to another due to:

- a) the size of organization and its type of activities, processes, products and services;
- b) the complexity of processes and their interactions; and
- c) the competence of persons.

# 7.5.2 Creating and updating

When creating and updating documented information the organization shall ensure appropriate:

- a) identification and description (e.g. a title, date, author, or reference number);
- b) format (e.g. language, software version, graphics) and media (e.g. paper, electronic); and
- c) review and approval for suitability and adequacy.

# 7.5.3 Control of documented information

Documented information required by the information security management system and by this International Standard shall be controlled to ensure:

- a) it is available and suitable for use, where and when it is needed; and
- b) it is adequately protected (e.g. from loss of confidentiality, improper use, or loss of integrity).

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

For the control of documented information, the organization shall address the following activities, as applicable:

- c) distribution, access, retrieval and use;
- d) storage and preservation, including the preservation of legibility;
- e) control of changes (e.g. version control); and
- f) retention and disposition.

Documented information of external origin, determined by the organization to be necessary for the planning and operation of the information security management system, shall be identified as appropriate, and controlled.

NOTE Access implies a decision regarding the permission to view the documented information only, or the permission and authority to view and change the documented information, etc.

# 8 Operation

# 8.1 Operational planning and control

The organization shall plan, implement and control the processes needed to meet information security requirements, and to implement the actions determined in 6.1. The organization shall also implement plans to achieve information security objectives determined in 6.2.

The organization shall keep documented information to the extent necessary to have confidence that the processes have been carried out as planned.

The organization shall control planned changes and review the consequences of unintended changes, taking action to mitigate any adverse effects, as necessary.

The organization shall ensure that outsourced processes are determined and controlled.

# 8.2 Information security risk assessment

The organization shall perform information security risk assessments at planned intervals or when significant changes are proposed or occur, taking account of the criteria established in 6.1.2 a).

The organization shall retain documented information of the results of the information security risk assessments.

# 8.3 Information security risk treatment

The organization shall implement the information security risk treatment plan.

The organization shall retain documented information of the results of the information security risk treatment.

# 9 Performance evaluation

# 9.1 Monitoring, measurement, analysis and evaluation

The organization shall evaluate the information security performance and the effectiveness of the information security management system.

The organization shall determine:

- a) what needs to be monitored and measured, including information security processes and controls;

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

b) the methods for monitoring, measurement, analysis and evaluation, as applicable, to ensure valid results;

NOTE The methods selected should produce comparable and reproducible results to be considered valid.

c) when the monitoring and measuring shall be performed;

d) who shall monitor and measure;

e) when the results from monitoring and measurement shall be analysed and evaluated; and

f) who shall analyse and evaluate these results.

The organization shall retain appropriate documented information as evidence of the monitoring and measurement results.

# 9.2 Internal audit

The organization shall conduct internal audits at planned intervals to provide information on whether the information security management system:

a) conforms to

1. the organization’s own requirements for its information security management system; and
2. the requirements of this International Standard;

b) is effectively implemented and maintained.

The organization shall:

1. plan, establish, implement and maintain an audit programme(s), including the frequency, methods, responsibilities, planning requirements and reporting. The audit programme(s) shall take into consideration the importance of the processes concerned and the results of previous audits;
2. define the audit criteria and scope for each audit;
3. select auditors and conduct audits that ensure objectivity and the impartiality of the audit process;
4. ensure that the results of the audits are reported to relevant management; and
5. retain documented information as evidence of the audit programme(s) and the audit results.

# 9.3 Management review

Top management shall review the organization’s information security management system at planned intervals to ensure its continuing suitability, adequacy and effectiveness.

The management review shall include consideration of:

1. the status of actions from previous management reviews;
2. changes in external and internal issues that are relevant to the information security management system;
3. feedback on the information security performance, including trends in:

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# 10 Improvement

# 10.1 Nonconformity and corrective action

When a nonconformity occurs, the organization shall:

1. react to the nonconformity, and as applicable:
1. take action to control and correct it; and
2. deal with the consequences;
2. evaluate the need for action to eliminate the causes of nonconformity, in order that it does not recur or occur elsewhere, by:
1. reviewing the nonconformity;
2. determining the causes of the nonconformity; and
3. determining if similar nonconformities exist, or could potentially occur;
3. implement any action needed;
4. review the effectiveness of any corrective action taken; and
5. make changes to the information security management system, if necessary.

Corrective actions shall be appropriate to the effects of the nonconformities encountered.

The organization shall retain documented information as evidence of:

1. the nature of the nonconformities and any subsequent actions taken, and
2. the results of any corrective action.

# 10.2 Continual improvement

The organization shall continually improve the suitability, adequacy and effectiveness of the information security management system.

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Annex A (normative)

# Reference control objectives and controls

The control objectives and controls listed in Table A.1 are directly derived from and aligned with those listed in ISO/IEC 27002:2013[1], Clauses 5 to 18 and are to be used in context with Clause 6.1.3.

| A.5        | Information security policies                                                                                                                                                     |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.5.1      | Management direction for information security                                                                                                                                     |
| Objective: | To provide management direction and support for information security in accordance with business requirements and relevant laws and regulations.                                  |
| A.5.1.1    | Policies for information security                                                                                                                                                 |
| Control    | A set of policies for information security shall be defined, approved by management, published and communicated to employees and relevant external parties.                       |
| A.5.1.2    | Review of the policies for information security                                                                                                                                   |
| Control    | The policies for information security shall be reviewed at planned intervals or if significant changes occur to ensure their continuing suitability, adequacy and effectiveness.  |
| A.6        | Organization of information security                                                                                                                                              |
| A.6.1      | Internal organization                                                                                                                                                             |
| Objective: | To establish a management framework to initiate and control the implementation and operation of information security within the organization.                                     |
| A.6.1.1    | Information security roles and responsibilities                                                                                                                                   |
| Control    | All information security responsibilities shall be defined and allocated.                                                                                                         |
| A.6.1.2    | Segregation of duties                                                                                                                                                             |
| Control    | Conflicting duties and areas of responsibility shall be segregated to reduce opportunities for unauthorized or unintentional modification or misuse of the organization’s assets. |
| A.6.1.3    | Contact with authorities                                                                                                                                                          |
| Control    | Appropriate contacts with relevant authorities shall be maintained.                                                                                                               |
| A.6.1.4    | Contact with special interest groups                                                                                                                                              |
| Control    | Appropriate contacts with special interest groups or other special security forums and professional associations shall be maintained.                                             |
| A.6.1.5    | Information security in project management                                                                                                                                        |
| Control    | Information security shall be addressed in project management, regardless of the type of the project.                                                                             |
| A.6.2      | Mobile devices and teleworking                                                                                                                                                    |
| Objective: | To ensure the security of teleworking and use of mobile devices.                                                                                                                  |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

# Control

# A.6.2.1 Mobile device policy

A policy and supporting security measures shall be adopted to manage the risks introduced by using mobile devices.

# Control

# A.6.2.2 Teleworking

A policy and supporting security measures shall be implemented to protect information accessed, processed or stored at teleworking sites.

# A.7 Human resource security

# A.7.1 Prior to employment

Objective: To ensure that employees and contractors understand their responsibilities and are suitable for the roles for which they are considered.

# Control

# A.7.1.1 Screening

Background verification checks on all candidates for employment shall be carried out in accordance with relevant laws, regulations and ethics and shall be proportional to the business requirements, the classification of the information to be accessed and the perceived risks.

# Control

# A.7.1.2 Terms and conditions of employment

The contractual agreements with employees and contractors shall state their and the organization’s responsibilities for information security.

# A.7.2 During employment

Objective: To ensure that employees and contractors are aware of and fulfil their information security responsibilities.

# Control

# A.7.2.1 Management responsibilities

Management shall require all employees and contractors to apply information security in accordance with the established policies and procedures of the organization.

# Control

# A.7.2.2 Information security awareness, education and training

All employees of the organization and, where relevant, contractors shall receive appropriate awareness education and training and regular updates in organizational policies and procedures, as relevant for their job function.

# Control

# A.7.2.3 Disciplinary process

There shall be a formal and communicated disciplinary process in place to take action against employees who have committed an information security breach.

# A.7.3 Termination and change of employment

Objective: To protect the organization’s interests as part of the process of changing or terminating employment.

# Control

# A.7.3.1 Termination or change of employment responsibilities

Information security responsibilities and duties that remain valid after termination or change of employment shall be defined, communicated to the employee or contractor and enforced.

# A.8 Asset management

# A.8.1 Responsibility for assets

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

Objective: To identify organizational assets and define appropriate protection responsibilities.

| A.8.1.1 | Inventory of assets      | Assets associated with information and information processing facilities shall be identified and an inventory of these assets shall be drawn up and maintained.              |
| ------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.8.1.2 | Ownership of assets      | Assets maintained in the inventory shall be owned.                                                                                                                           |
| A.8.1.3 | Acceptable use of assets | Rules for the acceptable use of information and of assets associated with information and information processing facilities shall be identified, documented and implemented. |
| A.8.1.4 | Return of assets         | All employees and external party users shall return all of the organizational assets in their possession upon termination of their employment, contract or agreement.        |

# A.8.2 Information classification

Objective: To ensure that information receives an appropriate level of protection in accordance with its importance to the organization.

| A.8.2.1 | Classification of information | Information shall be classified in terms of legal requirements, value, criticality and sensitivity to unauthorized disclosure or modification.                                      |
| ------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.8.2.2 | Labelling of information      | An appropriate set of procedures for information labelling shall be developed and implemented in accordance with the information classification scheme adopted by the organization. |
| A.8.2.3 | Handling of assets            | Procedures for handling assets shall be developed and implemented in accordance with the information classification scheme adopted by the organization.                             |

# A.8.3 Media handling

Objective: To prevent unauthorized disclosure, modification, removal or destruction of information stored on media.

| A.8.3.1 | Management of removable media | Procedures shall be implemented for the management of removable media in accordance with the classification scheme adopted by the organization. |
| ------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| A.8.3.2 | Disposal of media             | Media shall be disposed of securely when no longer required, using formal procedures.                                                           |
| A.8.3.3 | Physical media transfer       | Media containing information shall be protected against unauthorized access, misuse or corruption during transportation.                        |

# A.9 Access control

# A.9.1 Business requirements of access control

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

# Objective:

To limit access to information and information processing facilities.

| Control | Description                                                                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.9.1.1 | Access control policy: An access control policy shall be established, documented and reviewed based on business and information security requirements.                    |
| A.9.1.2 | Access to networks and network services: Users shall only be provided with access to the network and network services that they have been specifically authorized to use. |

# A.9.2 User access management

# Objective:

To ensure authorized user access and to prevent unauthorized access to systems and services.

| Control | Description                                                                                                                                                                                                                                                     |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.9.2.1 | User registration and de registration: A formal user registration and de registration process shall be implemented to enable assignment of access rights.                                                                                                       |
| A.9.2.2 | User access provisioning: A formal user access provisioning process shall be implemented to assign or revoke access rights for all user types to all systems and services.                                                                                      |
| A.9.2.3 | Management of privileged access rights: The allocation and use of privileged access rights shall be restricted and controlled.                                                                                                                                  |
| A.9.2.4 | Management of secret authentication information of users: The allocation of secret authentication information shall be controlled through a formal management process.                                                                                          |
| A.9.2.5 | Review of user access rights: Asset owners shall review users’ access rights at regular intervals.                                                                                                                                                              |
| A.9.2.6 | Removal or adjustment of access rights: The access rights of all employees and external party users to information and information processing facilities shall be removed upon termination of their employment, contract or agreement, or adjusted upon change. |

# A.9.3 User responsibilities

# Objective:

To make users accountable for safeguarding their authentication information.

| Control | Description                                                                                                                                               |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.9.3.1 | Use of secret authentication information: Users shall be required to follow the organization’s practices in the use of secret authentication information. |

# A.9.4 System and application access control

# Objective:

To prevent unauthorized access to systems and applications.

| Control | Description                                                                                                                                                 |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.9.4.1 | Information access restriction: Access to information and application system functions shall be restricted in accordance with the access control policy.    |
| A.9.4.2 | Secure log on procedures: Where required by the access control policy, access to systems and applications shall be controlled by a secure log-on procedure. |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

| A.9.4.3  | Password management system                                                                                                                                  | Control                                                                                                                                                                                                                                   |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|          | Password management systems shall be interactive and shall ensure quality passwords.                                                                        |                                                                                                                                                                                                                                           |
| A.9.4.4  | Use of privileged utility programs                                                                                                                          | The use of utility programs that might be capable of overriding system and application controls shall be restricted and tightly controlled.                                                                                               |
| A.9.4.5  | Access control to program source code                                                                                                                       | Control                                                                                                                                                                                                                                   |
|          | Access to program source code shall be restricted.                                                                                                          |                                                                                                                                                                                                                                           |
| A.10     | Cryptography                                                                                                                                                |                                                                                                                                                                                                                                           |
| A.10.1   | Cryptographic controls                                                                                                                                      | Objective: To ensure proper and effective use of cryptography to protect the confidentiality, authenticity and/or integrity of information.                                                                                               |
| A.10.1.1 | Policy on the use of cryptographic controls                                                                                                                 | Control                                                                                                                                                                                                                                   |
|          | A policy on the use of cryptographic controls for protection of information shall be developed and implemented.                                             |                                                                                                                                                                                                                                           |
| A.10.1.2 | Key management                                                                                                                                              | A policy on the use, protection and lifetime of cryptographic keys shall be developed and implemented through their whole lifecycle.                                                                                                      |
| A.11     | Physical and environmental security                                                                                                                         |                                                                                                                                                                                                                                           |
| A.11.1   | Secure areas                                                                                                                                                | Objective: To prevent unauthorized physical access, damage and interference to the organization’s information and information processing facilities.                                                                                      |
| A.11.1.1 | Physical security perimeter                                                                                                                                 | Control                                                                                                                                                                                                                                   |
|          | Security perimeters shall be defined and used to protect areas that contain either sensitive or critical information and information processing facilities. |                                                                                                                                                                                                                                           |
| A.11.1.2 | Physical entry controls                                                                                                                                     | Secure areas shall be protected by appropriate entry controls to ensure that only authorized personnel are allowed access.                                                                                                                |
| A.11.1.3 | Securing offices, rooms and facilities                                                                                                                      | Control                                                                                                                                                                                                                                   |
|          | Physical security for offices, rooms and facilities shall be designed and applied.                                                                          |                                                                                                                                                                                                                                           |
| A.11.1.4 | Protecting against external and environmental threats                                                                                                       | Control                                                                                                                                                                                                                                   |
|          | Physical protection against natural disasters, malicious attack or accidents shall be designed and applied.                                                 |                                                                                                                                                                                                                                           |
| A.11.1.5 | Working in secure areas                                                                                                                                     | Control                                                                                                                                                                                                                                   |
|          | Procedures for working in secure areas shall be designed and applied.                                                                                       |                                                                                                                                                                                                                                           |
| A.11.1.6 | Delivery and loading areas                                                                                                                                  | Access points such as delivery and loading areas and other points where unauthorized persons could enter the premises shall be controlled and, if possible, isolated from information processing facilities to avoid unauthorized access. |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

# A.11.2 Equipment

Objective: To prevent loss, damage, theft or compromise of assets and interruption to the organization’s operations.

# Control

A.11.2.1 Equipment siting and protection

Equipment shall be sited and protected to reduce the risks from environmental threats and hazards, and opportunities for unauthorized access.

# Control

A.11.2.2 Supporting utilities

Equipment shall be protected from power failures and other disruptions caused by failures in supporting utilities.

# Control

A.11.2.3 Cabling security

Power and telecommunications cabling carrying data or supporting information services shall be protected from interception, interference or damage.

# Control

A.11.2.4 Equipment maintenance

Equipment shall be correctly maintained to ensure its continued availability and integrity.

# Control

A.11.2.5 Removal of assets

Equipment, information or software shall not be taken off site without prior authorization.

# Control

A.11.2.6 Security of equipment and assets off premises

Security shall be applied to off-site assets taking into account the different risks of working outside the organization’s premises.

# Control

A.11.2.7 Secure disposal or reuse of equipment

All items of equipment containing storage media shall be verified to ensure that any sensitive data and licensed software has been removed or securely overwritten prior to disposal or re-use.

# Control

A.11.2.8 Unattended user equipment

Users shall ensure that unattended equipment has appropriate protection.

# Control

A.11.2.9 Clear desk and clear screen policy

A clear desk policy for papers and removable storage media and a clear screen policy for information processing facilities shall be adopted.

# A.12 Operations security

# A.12.1 Operational procedures and responsibilities

Objective: To ensure correct and secure operations of information processing facilities.

# Control

A.12.1.1 Documented operating procedures

Operating procedures shall be documented and made available to all users who need them.

# Control

A.12.1.2 Change management

Changes to the organization, business processes, information processing facilities and systems that affect information security shall be controlled.

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

# A.12.1 Capacity management

# A.12.1.3 Control

The use of resources shall be monitored, tuned and projections made of future capacity requirements to ensure the required system performance.

# Separation of development, testing and operational environments

# A.12.1.4 Control

Development, testing, and operational environments shall be separated to reduce the risks of unauthorized access or changes to the operational environment.

# A.12.2 Protection from malware

Objective: To ensure that information and information processing facilities are protected against malware.

# A.12.2.1 Control

Detection, prevention and recovery controls to protect against malware shall be implemented, combined with appropriate user awareness.

# A.12.3 Backup

Objective: To protect against loss of data.

# A.12.3.1 Control

Backup copies of information, software and system images shall be taken and tested regularly in accordance with an agreed backup policy.

# A.12.4 Logging and monitoring

Objective: To record events and generate evidence.

# A.12.4.1 Control

Event logs recording user activities, exceptions, faults and information security events shall be produced, kept and regularly reviewed.

# A.12.4.2 Control

Logging facilities and log information shall be protected against tampering and unauthorized access.

# A.12.4.3 Control

System administrator and system operator activities shall be logged and the logs protected and regularly reviewed.

# A.12.4.4 Control

The clocks of all relevant information processing systems within an organization or security domain shall be synchronised to a single reference time source.

# A.12.5 Control of operational software

Objective: To ensure the integrity of operational systems.

# A.12.5.1 Control

Procedures shall be implemented to control the installation of software on operational systems.

# A.12.6 Technical vulnerability management

Objective: To prevent exploitation of technical vulnerabilities.

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

| A.12.6.1 | Management of technical vulnerabilities      | Information about technical vulnerabilities of information systems being used shall be obtained in a timely fashion, the organization’s exposure to such vulnerabilities evaluated and appropriate measures taken to address the associated risk. |
| -------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.12.6.2 | Restrictions on software installation        | Rules governing the installation of software by users shall be established and implemented.                                                                                                                                                       |
| A.12.7   | Information systems audit considerations     | Objective: To minimise the impact of audit activities on operational systems.                                                                                                                                                                     |
| A.12.7.1 | Information systems audit controls           | Audit requirements and activities involving verification of operational systems shall be carefully planned and agreed to minimise disruptions to business processes.                                                                              |
| A.13     | Communications security                      |                                                                                                                                                                                                                                                   |
| A.13.1   | Network security management                  | Objective: To ensure the protection of information in networks and its supporting information processing facilities.                                                                                                                              |
| A.13.1.1 | Network controls                             | Networks shall be managed and controlled to protect information in systems and applications.                                                                                                                                                      |
| A.13.1.2 | Security of network services                 | Security mechanisms, service levels and management requirements of all network services shall be identified and included in network services agreements, whether these services are provided in house or outsourced.                              |
| A.13.1.3 | Segregation in networks                      | Groups of information services, users and information systems shall be segregated on networks.                                                                                                                                                    |
| A.13.2   | Information transfer                         | Objective: To maintain the security of information transferred within an organization and with any external entity.                                                                                                                               |
| A.13.2.1 | Information transfer policies and procedures | Formal transfer policies, procedures and controls shall be in place to protect the transfer of information through the use of all types of communication facilities.                                                                              |
| A.13.2.2 | Agreements on information transfer           | Agreements shall address the secure transfer of business information between the organization and external parties.                                                                                                                               |
| A.13.2.3 | Electronic messaging                         | Information involved in electronic messaging shall be appropriately protected.                                                                                                                                                                    |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

| A.13.2.4 | Confidentiality or non-disclosure agreements | Requirements for confidentiality or non-disclosure agreements reflecting the organization’s needs for the protection of information shall be identified, regularly reviewed and documented. |
| -------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

# A.14 System acquisition, development and maintenance

# A.14.1 Security requirements of information systems

Objective: To ensure that information security is an integral part of information systems across the entire lifecycle. This also includes the requirements for information systems which provide services over public networks.

| A.14.1.1 | Security requirements analysis and specification | The information security related requirements shall be included in the requirements for new information systems or enhancements to existing information systems.                                                                   |
| -------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.14.1.2 | Securing application services on public networks | Information involved in application services passing over public networks shall be protected from fraudulent activity, contract dispute and unauthorized disclosure and modification.                                              |
| A.14.1.3 | Protecting application services transactions     | Information involved in application service transactions shall be protected to prevent incomplete transmission, mis routing, unauthorized message alteration, unauthorized disclosure, unauthorized message duplication or replay. |

# A.14.2 Security in development and support processes

Objective: To ensure that information security is designed and implemented within the development lifecycle of information systems.

| A.14.2.1 | Secure development policy                                         | Rules for the development of software and systems shall be established and applied to developments within the organization.                                                      |
| -------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.14.2.2 | System change control procedures                                  | Changes to systems within the development lifecycle shall be controlled by the use of formal change control procedures.                                                          |
| A.14.2.3 | Technical review of applications after operating platform changes | When operating platforms are changed, business critical applications shall be reviewed and tested to ensure there is no adverse impact on organizational operations or security. |
| A.14.2.4 | Restrictions on changes to software packages                      | Modifications to software packages shall be discouraged, limited to necessary changes and all changes shall be strictly controlled.                                              |
| A.14.2.5 | Secure system engineering principles                              | Principles for engineering secure systems shall be established, documented, maintained and applied to any information system implementation efforts.                             |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

| A.14.2.6 | Secure development environment | Organizations shall establish and appropriately protect secure development environments for system development and integration efforts that cover the entire system development lifecycle. |
| -------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A.14.2.7 | Outsourced development         | The organization shall supervise and monitor the activity of outsourced system development.                                                                                                |
| A.14.2.8 | System security testing        | Testing of security functionality shall be carried out during development.                                                                                                                 |
| A.14.2.9 | System acceptance testing      | Acceptance testing programs and related criteria shall be established for new information systems, upgrades and new versions.                                                              |

# A.14.3 Test data

Objective: To ensure the protection of data used for testing.

| A.14.3.1 | Protection of test data | Test data shall be selected carefully, protected and controlled. |
| -------- | ----------------------- | ---------------------------------------------------------------- |

# A.15 Supplier relationships

# A.15.1 Information security in supplier relationships

Objective: To ensure protection of the organization’s assets that is accessible by suppliers.

| Information security                     | Control                                        |                                                                                                                                                                                                                              |
| ---------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.15.1.1                                 | policy for supplier relationships              | Information security requirements for mitigating the risks associated with supplier’s access to the organization’s assets shall be agreed with the supplier and documented.                                                  |
| A.15.1.2                                 | Addressing security within supplier agreements | All relevant information security requirements shall be established and agreed with each supplier that may access, process, store, communicate, or provide IT infrastructure components for, the organization’s information. |
| Information and communication technology | Control                                        |                                                                                                                                                                                                                              |
| A.15.1.3                                 | supply chain                                   | Agreements with suppliers shall include requirements to address the information security risks associated with information and communications technology services and product supply chain.                                  |

# A.15.2 Supplier service delivery management

Objective: To maintain an agreed level of information security and service delivery in line with supplier agreements.

| A.15.2.1 | Monitoring and review of supplier services | Organizations shall regularly monitor, review and audit supplier service delivery.                                                                                                                                                                                                              |
| -------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.15.2.2 | Managing changes to supplier services      | Changes to the provision of services by suppliers, including maintaining and improving existing information security policies, procedures and controls, shall be managed, taking account of the criticality of business information, systems and processes involved and re-assessment of risks. |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

# A.16 Information security incident management

# A.16.1 Management of information security incidents and improvements

Objective: To ensure a consistent and effective approach to the management of information security incidents, including communication on security events and weaknesses.

| A.16.1.1 | Responsibilities and procedures                           | Management responsibilities and procedures shall be established to ensure a quick, effective and orderly response to information security incidents.                                                       |
| -------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.16.1.2 | Reporting information security events                     | Information security events shall be reported through appropriate management channels as quickly as possible.                                                                                              |
| A.16.1.3 | Reporting information security weaknesses                 | Employees and contractors using the organization’s information systems and services shall be required to note and report any observed or suspected information security weaknesses in systems or services. |
| A.16.1.4 | Assessment of and decision on information security events | Information security events shall be assessed and it shall be decided if they are to be classified as information security incidents.                                                                      |
| A.16.1.5 | Response to information security incidents                | Information security incidents shall be responded to in accordance with the documented procedures.                                                                                                         |
| A.16.1.6 | Learning from information security incidents              | Knowledge gained from analysing and resolving information security incidents shall be used to reduce the likelihood or impact of future incidents.                                                         |
| A.16.1.7 | Collection of evidence                                    | The organization shall define and apply procedures for the identification, collection, acquisition and preservation of information, which can serve as evidence.                                           |

# A.17 Information security aspects of business continuity management

# A.17.1 Information security continuity

Objective: Information security continuity shall be embedded in the organization’s business continuity management systems.

| A.17.1.1 | Planning information security continuity     | The organization shall determine its requirements for information security and the continuity of information security management in adverse situations, e.g. during a crisis or disaster.              |
| -------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A.17.1.2 | Implementing information security continuity | The organization shall establish, document, implement and maintain processes, procedures and controls to ensure the required level of continuity for information security during an adverse situation. |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

| A.17.1.3 | Verify, review and evaluate information security continuity           | The organization shall verify the established and implemented information security continuity controls at regular intervals in order to ensure that they are valid and effective during adverse situations.                                                                  |
| -------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.17.2   | Redundancies                                                          | Objective: To ensure availability of information processing facilities.                                                                                                                                                                                                      |
| A.17.2.1 | Availability of information processing facilities                     | Information processing facilities shall be implemented with redundancy sufficient to meet availability requirements.                                                                                                                                                         |
| A.18     | Compliance                                                            |                                                                                                                                                                                                                                                                              |
| A.18.1   | Compliance with legal and contractual requirements                    | Objective: To avoid breaches of legal, statutory, regulatory or contractual obligations related to information security and of any security requirements.                                                                                                                    |
| A.18.1.1 | Identification of applicable legislation and contractual requirements | All relevant legislative statutory, regulatory, contractual requirements and the organization’s approach to meet these requirements shall be explicitly identified, documented and kept up to date for each information system and the organization.                         |
| A.18.1.2 | Intellectual property rights                                          | Appropriate procedures shall be implemented to ensure compliance with legislative, regulatory and contractual requirements related to intellectual property rights and use of proprietary software products.                                                                 |
| A.18.1.3 | Protection of records                                                 | Records shall be protected from loss, destruction, falsification, unauthorized access and unauthorized release, in accordance with legislatory, regulatory, contractual and business requirements.                                                                           |
| A.18.1.4 | Privacy and protection of personally identifiable information         | Privacy and protection of personally identifiable information shall be ensured as required in relevant legislation and regulation where applicable.                                                                                                                          |
| A.18.1.5 | Regulation of cryptographic controls                                  | Cryptographic controls shall be used in compliance with all relevant agreements, legislation and regulations.                                                                                                                                                                |
| A.18.2   | Information security reviews                                          | Objective: To ensure that information security is implemented and operated in accordance with the organizational policies and procedures.                                                                                                                                    |
| A.18.2.1 | Independent review of information security                            | The organization’s approach to managing information security and its implementation (i.e. control objectives, controls, policies, processes and procedures for information security) shall be reviewed independently at planned intervals or when significant changes occur. |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Table A.1 (continued)

| A.18.2.2 | Compliance with security policies and standards | Managers shall regularly review the compliance of information processing and procedures within their area of responsibility with the appropriate security policies, standards and any other security requirements. |
| -------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A.18.2.3 | Technical compliance review                     | Information systems shall be regularly reviewed for compliance with the organization’s information security policies and standards.                                                                                |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

# Bibliography

| \[1] | ISO/IEC 27002:2013, Information technology — Security Techniques — Code of practice for information security controls             |
| ---- | --------------------------------------------------------------------------------------------------------------------------------- |
| \[2] | ISO/IEC 27003:2010, Information technology — Security techniques — Information security management system implementation guidance |
| \[3] | ISO/IEC 27004:2009, Information technology — Security techniques — Information security management — Measurement                  |
| \[4] | ISO/IEC 27005:2011, Information technology — Security techniques — Information security risk management                           |
| \[5] | ISO 31000:2009, Risk management — Principles and guidelines                                                                       |
| \[6] | ISO/IEC Directives, Part 1, Consolidated ISO Supplement – Procedures specific to ISO, 2012                                        |

© ISO/IEC 2013 – All rights reserved
---
# ISO/IEC 27001:2013(E)

ICS 35.040

Price based on 23 pages

© ISO/IEC 2013 – All rights reserved