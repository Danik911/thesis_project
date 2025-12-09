# ISPE GAMP 5: A Risk-Based Approach to Compliant GxP Computerized Systems (Second Edition)

*Management | Development | Operation | Special Interest | General | Critical Thinking | Enabling Innovation | Advancing Technologies*

---

**Citation Information:**
- **Title**: ISPE GAMP® 5 Guide: A Risk-Based Approach to Compliant GxP Computerized Systems (Second Edition)
- **Publisher**: International Society for Pharmaceutical Engineering (ISPE)
- **Year**: 2022
- **Copyright**: © 2022 ISPE. All rights reserved.
- **Document Type**: Industry guidance document for GxP regulatory compliance

**Disclaimer:** The Guide is meant to assist life-sciences companies in managing GxP regulated systems. This Guide is solely created and owned by ISPE. It is not a regulation, standard or regulatory guideline document.

---

# 1 Introduction

GAMP guidance aims to safeguard patient safety, product quality, and data integrity in the use of GxP computerized systems. It aims to achieve computerized systems that are fit for intended use and meet current regulatory requirements by building upon existing industry good practice in an efficient and effective manner.

GAMP provides practical guidance that:

- Facilitates the interpretation of regulatory requirements
- Establishes a common language and terminology
- Promotes a system life cycle approach based on good practice
- Clarifies roles and responsibilities

It is not a prescriptive method or a standard, but rather provides pragmatic guidance, approaches, and tools for the practitioner.

When applied with expertise and good judgment, this Guide offers a robust, cost-effective approach.

The approach described in this document is designed to be compatible with a wide range of other models, methods, and schemes including:

- Quality systems standards and certification schemes, such as the ISO 9000 Series [1]
- ISO 14971 [2]: Medical devices – Application of risk management to medical devices
- Schemes for assessing and improving organization capability and maturity, such as Capability Maturity Model Integration® (CMMI) [3]
- Software process models such as ISO 12207 [4]
- Iterative, and incremental (Agile) software development methods and models
- Approaches to IT service management, such as ITIL [5]

Where possible, terminology is harmonized with standard international sources such as ICH [6] and ISO [7].

This Guide aims to be fully compatible with the approach described in the ASTM E2500 Standard Guide for Specification, Design, and Verification of Pharmaceutical and Biopharmaceutical Manufacturing Systems and Equipment [8].

GAMP is an ISPE Community of Practice. For further information see www.ispe.org.

# 1.1 Rationale for GAMP 5 Second Edition

This Second Edition Guide aims to protect patient safety, product quality, and data integrity by facilitating and encouraging the achievement of computerized systems that are effective, reliable, and of high quality.

While the overall approach, framework, and key concepts remain unchanged, technical content of the Guide has been updated to reflect the increased importance of IT service providers including cloud service providers, evolving approaches to software development including incremental and iterative models and methods, and increased use of software tools and automation to achieve greater control, higher quality, and lower risks throughout the life cycle.

Associated with this is the reinforcement of the message that the GAMP specification and verification approach is not inherently linear but also fully supports iterative and incremental (Agile) methods.

Guidance on the application of new and developing technological areas such as Artificial Intelligence and Machine Learning (AI/ML), blockchain, cloud computing, and Open-Source Software (OSS) has been included or updated.

The importance of critical thinking and the application of patient-centric, risk-based approaches (aimed at quality and safety) versus primarily compliance-driven approaches is further underlined. Concepts of computerized systems assurance as discussed as part of the US FDA Center for Devices and Radiological Health (CDRH) Case for Quality program [9] are also explored and applied.

Links and references to GAMP guidance on the topic area of record and data integrity have been added.

The following ISPE initiatives and topic areas are supported and links and synergies with them have been considered:

- Knowledge Management – focusing on how organizations create, manage, and use knowledge throughout the life cycle of a product, enabling organizations to better manage their knowledge as a key asset, in turn improving the effectiveness of the pharmaceutical quality system, and providing operational benefits. [10]
- APQ (Advancing Pharmaceutical Quality) – building industry-for-industry tools and programs to help companies assess and improve their quality operations. [11]
- Pharma 4.0™ – providing guidance, aligned with the regulatory requirements specific to the pharmaceutical industry, to accelerate Pharma 4.0 transformations. Also known as the Smart Factory, the objective of Pharma 4.0 is to enable organizations involved in the product life cycle to leverage the full potential of digitalization to provide faster innovations for the benefit of patients. [12]

Digital maturity and data integrity by design are enablers to an effective digitalization strategy and are underpinned by well-managed automation and information systems. GAMP guidance aims to ensure that GxP computerized systems are fit for intended use, and that GxP electronic records and data are managed throughout the data life cycle in order to ensure data integrity.

GAMP guidance adopts a patient-centric risk-based approach that enables innovation while demonstrating compliance with regulatory requirements. Pharma 4.0 builds on best practices based on ISPE Guidelines that are enhanced by the digital transformational approach to real time data driven processes.

---

# 2 Key Concepts

# 2.1 Overview

Five key concepts are applied throughout this Guide:

1. Product and process understanding
2. Life cycle approach within a QMS
3. Scalable life cycle activities
4. Science-based QRM
5. Leveraging supplier involvement

The relationship between these concepts is shown in Figure 2.1.

Figure 2.1: Key Concepts of this Guide [20]

# 2.1.1 Product and Process Understanding

An understanding of the supported process is fundamental to determining system requirements. Product and process understanding is the basis for making science- and risk-based decisions to ensure that the system is fit for its intended use. An understanding of the intended use of data within the process is also fundamental. Data integrity cannot be achieved without a complete understanding of the data flow.

As noted in ICH Q10 [21]:

"product and process knowledge should be managed from development through the commercial life of the product up to and including product discontinuation…Knowledge management is a systematic approach to acquiring, analysing, storing, and disseminating information related to products, manufacturing processes and components."

Efforts to ensure fitness for intended use should focus on those aspects that are critical to patient safety, product quality, and data integrity. These critical aspects should be identified, specified, and verified.

Systems within the scope of this Guide support a wide range of processes, including but not limited to clinical trials, toxicological studies, API production, formulated product production, warehousing, distribution, and pharmacovigilance.

For some manufacturing systems, process requirements depend on a thorough understanding of product characteristics. For these systems, identification of Critical Quality Attributes (CQAs) and related Critical Process Parameters (CPPs) enable process control requirements to be defined.

Specification of requirements should be focused on critical aspects. The extent and detail of requirement specification should be commensurate with associated risk, complexity, and novelty of the system. Requirements may be developed iteratively or incrementally, based upon an initial set of base requirements.

Incomplete process understanding hinders effective and efficient compliance and achievement of business benefit.

# 2.1.2 Life Cycle Approach within a QMS

Adopting a complete computerized system life cycle entails defining activities in a systematic way from system conception to retirement. This enables management control and a consistent approach across systems.

The life cycle should form an intrinsic part of the company's QMS, which should be maintained and kept up-to-date as new ways of working are developed.

As experience is gained in system use, the QMS should enable continual process and system improvements based on periodic review and evaluation, operational and performance data, and root-cause analysis of failures. Identified improvements and corrective actions should follow change management.

A suitable life cycle, properly applied, enables the assurance of quality and fitness for intended use, and achieving and maintaining compliance with regulatory requirements. A well-managed and understood life cycle facilitates adoption of a Quality by Design (QbD) approach.

The life cycle approach is fundamental to this Guide and embodies each of the other key concepts. The life cycle is structured into phases and activities, as described in Chapter 3.

# 2.1.3 Scalable Life Cycle Activities

Life cycle activities should be scaled according to:

- System impact on patient safety, product quality, and data integrity (risk assessment)
- System complexity and novelty (architecture and nature of system components including maturity and level of configuration or customization)
- Outcome of supplier assessment (supplier capability)

Business impact also may influence the scaling of life cycle activities.

The strategy should be clearly defined in a plan and follow established and approved policies and procedures.

# 2.1.4 Science-Based Quality Risk Management

QRM is a systematic process for the identification, assessment, control, communication, mitigation, and review of risks. Application of QRM enables effort to be focused on critical aspects of a computerized system in a controlled and justified manner. QRM should be based on clear process understanding and potential impact on patient safety, product quality, and data integrity. Combining knowledge management and QRM will facilitate achievement of QMS objectives by providing the means for science- and risk-based decisions related to product quality. For systems controlling or monitoring CPPs, these should be traceable to CQAs, and ultimately back to the Quality Target Product Profile (QTPP) and relevant regulatory submissions. Qualitative or quantitative techniques may be used to identify and manage risks. Controls are developed to reduce risks to an acceptable level. Implemented controls are monitored during operation to ensure ongoing effectiveness. A practical risk-management process is described in Chapter 5.

# 2.1.5 Leveraging Supplier Involvement

Regulated companies should seek to maximize supplier involvement throughout the system life cycle in order to leverage knowledge, experience, and documentation, subject to satisfactory supplier assessment. For example, the supplier may assist with requirements gathering, risk assessments, the creation of functional and other specifications, system configuration, testing, support, and maintenance. Planning should determine how best to use supplier documentation, including existing test documentation, to avoid wasted effort and duplication. Justification for the use of supplier documentation should be provided by the satisfactory outcome of supplier assessments, which may include supplier audits. Documentation should be assessed for suitability, accuracy, and completeness. There should be flexibility regarding acceptable format, structure, and documentation practices. Supplier assessment is described in Chapter 6.

# 2.2 Key Terms

**Computerized System**: A computerized system consists of the hardware and software components, together with the controlled function or process (including procedures, people, and equipment and associated documentation) (see also Appendix M11).

**Computerized System Validation**: Documented evidence that a computerized system does what it purports to do, and that controls are maintained for the life of the system.

**GxP Compliance**: Meeting all applicable pharmaceutical and associated life-science regulatory requirements.

**GxP Regulated Computerized System**: Computerized systems that are subject to GxP regulations. The regulated company must ensure that such systems comply with the appropriate regulations.

**GxP Regulation**: The underlying international pharmaceutical requirements, such as those set forth in the US FD&C Act, US PHS Act, FDA regulations, EU Directives, Japanese regulations, or other applicable national legislation or regulations under which a company operates.

**Process Owner**: This is the owner of the business process or processes being managed. The process owner is ultimately responsible for ensuring that the computerized system and its operation is in compliance and fit for intended use in accordance with applicable company Standard Operating Procedures (SOPs).

**Quality Management System (QMS)**: Part of a management system with regard to quality. A management system is a set of interrelated or interacting elements of an organization to establish policies and objectives, and processes to achieve those objectives.

**Subject Matter Expert (SME)**: An individual with specific expertise in a particular area or topic.

**System Owner**: This is the owner of the computerized system. The system owner is ultimately responsible for the availability, integrity, and security of the computerized system and for ensuring that it is maintained in a validated state.

---

# 3 Life Cycle Approach

Compliance with regulatory requirements and fitness for intended use may be achieved by adopting a life cycle approach following good practice as defined in this Guide.

A life cycle approach entails defining and performing activities in a systematic way from conception, understanding the requirements, through development, release, and operational use, to system retirement. Figure 3.1 shows a general specification, design, and verification process described in ASTM E2500 [8].

This section of the Guide introduces the computerized system life cycle, a general approach to specification and verification, a framework for computerized system validation, and the application of critical thinking.

# 3.1 Computerized System Life Cycle

The computerized system life cycle encompasses all activities from initial concept to retirement.

The life cycle for any system consists of four major phases:

- **Concept**: Activities that occur before the project formally begins, including strategic planning, initial risk assessment, and system analysis.
- **Project**: Activities associated with the creation, configuration, and implementation of the computerized system.
- **Operation**: Activities associated with the use of the computerized system in the business environment.
- **Retirement**: Activities associated with the withdrawal of the computerized system from use.

These phases are not necessarily sequential. Some activities may occur concurrently or iteratively.

# 3.2 Specification and Verification

The GAMP specification and verification approach is not inherently linear; it also fully supports iterative and incremental (Agile) methods.

The approach is based on the principle that systems should be specified by users and verified by testing. This ensures that the system will meet the user's requirements and that it is fit for its intended use.

## 3.2.1 Linear Approach

In a linear approach, each specification level is completed before moving to the next level. Testing is conducted in reverse order to specification.

## 3.2.2 Iterative Approach

In an iterative approach, the system is developed and tested through a series of iterations, with each iteration building upon the previous one. This approach allows for early validation of system functionality and enables changes to be made more easily.

# 3.3 Computerized System Validation Framework

GAMP advocates a computerized system validation framework to achieve and maintain GxP compliance throughout the computerized system life cycle.

The framework consists of:

- **Quality Management System**: Provides the overall framework for managing quality throughout the system life cycle.
- **Life Cycle Activities**: Systematic activities performed throughout the system life cycle.
- **Supporting Processes**: Processes that support the life cycle activities, including risk management, change management, and design review.
- **Records and Documentation**: Evidence of compliance with regulatory requirements and system fitness for intended use.

# 3.4 Critical Thinking Through the Life Cycle

Critical thinking promotes informed decision-making and good judgment on where and how to apply and scale quality and compliance activities for computerized systems.

Critical thinking should be applied throughout the life cycle to:

- Determine appropriate levels of effort for life cycle activities
- Identify and assess risks
- Make decisions about control strategies
- Evaluate the effectiveness of implemented controls
- Ensure that systems remain fit for their intended use

Critical thinking is not about reducing effort or cutting corners; it is about applying effort effectively where it is most needed.

---

# 4 Life Cycle Phases

This section further describes the phases of the computerized system life cycle introduced in Chapter 3. The life cycle approach described is not inherently linear, and is designed to be compatible with a wide range of models and methods, including iterative and incremental (Agile) approaches.

# 4.1 Concept

Detailed activities in this phase will depend on company approaches to initiating and justifying project commencement. Gaining management commitment to provide appropriate resources is an important pre-project activity.

Key activities in the concept phase include:

- **Strategic Planning**: Defining the business need and objectives for the computerized system.
- **Initial Risk Assessment**: Identifying potential risks and their impact on patient safety, product quality, and data integrity.
- **System Analysis**: Understanding the current state and defining the future state requirements.
- **Feasibility Study**: Evaluating the technical and business feasibility of the proposed solution.
- **Business Case Development**: Documenting the justification for the project.

# 4.2 Project

This section describes the following project stages in more detail:

- Planning
- Specification, configuration, and coding
- Verification
- Reporting and release

## 4.2.1 Planning

Planning activities include:

- **Project Planning**: Defining the project scope, objectives, deliverables, and timelines.
- **Quality Planning**: Defining the quality management approach for the project.
- **Risk Management Planning**: Defining the risk management approach and identifying initial risks.
- **Resource Planning**: Identifying required resources and ensuring their availability.
- **Supplier Management**: Selecting and managing suppliers involved in the project.

## 4.2.2 Specification, Configuration, and Coding

This stage involves:

- **User Requirements Specification (URS)**: Defining what the system should do from the user's perspective.
- **Functional Specification (FS)**: Defining how the system will meet the user requirements.
- **Design Specification (DS)**: Defining the detailed design of the system.
- **System Configuration**: Configuring the system to meet the specifications.
- **Custom Code Development**: Developing custom software components as needed.

## 4.2.3 Verification

Verification activities include:

- **Installation Qualification (IQ)**: Verifying that the system has been installed correctly.
- **Operational Qualification (OQ)**: Verifying that the system operates as intended.
- **Performance Qualification (PQ)**: Verifying that the system performs consistently in its intended environment.
- **User Acceptance Testing (UAT)**: Verifying that the system meets user requirements.

## 4.2.4 Reporting and Release

This stage involves:

- **Validation Reporting**: Documenting the validation activities and results.
- **System Release**: Formally releasing the system for operational use.
- **Handover**: Transferring the system from the project team to the operational team.

## 4.2.5 Supporting Processes

Supporting processes include:

- **Risk Management**: Ongoing identification, assessment, and mitigation of risks.
- **Change Management**: Managing changes to the system throughout the project.
- **Design Review**: Reviewing system design to ensure it meets requirements.
- **Traceability**: Maintaining traceability between requirements, specifications, and test results.
- **Documentation Management**: Managing project documentation and records.

# 4.3 Operation

This section provides guidance on system operation. Not all the activities will be directly relevant to all systems. The approach and required activities should be selected and scaled according to the nature, risk, and complexity of the system in question through the application of critical thinking.

Key operational activities include:

- **System Handover**: Transferring the system from the project team to the operational team.
- **Service Management**: Managing the ongoing operation and support of the system.
- **Incident Management**: Managing incidents and problems that occur during operation.
- **Change Management**: Managing changes to the system during operation.
- **Performance Management**: Monitoring and managing system performance.
- **Security Management**: Ensuring the security of the system and its data.
- **Backup and Recovery**: Ensuring that system data can be recovered in the event of failure.
- **Periodic Review**: Regularly reviewing the system to ensure it remains fit for its intended use.

# 4.4 Retirement

This activity covers system withdrawal, system decommissioning, system disposal, and migration of required data.

Key retirement activities include:

- **Retirement Planning**: Planning for the retirement of the system.
- **Data Migration**: Migrating data from the retiring system to a new system or archive.
- **System Decommissioning**: Safely shutting down and removing the system.
- **Data Retention**: Ensuring that required data is retained in accordance with regulatory requirements.
- **Asset Disposal**: Properly disposing of system hardware and software.

---

# 5 Quality Risk Management

Chapter 3 introduced the concept of QRM as part of the life cycle approach. This section gives an overview of the QRM process and Appendix M3 provides more detail.

# 5.1 Overview

QRM is a systematic process for the assessment, control, communication, and review of risks. It is an iterative process used throughout the computerized system life cycle from concept to retirement.

The objectives of QRM are to:

- Identify potential risks to patient safety, product quality, and data integrity
- Assess the significance of these risks
- Implement controls to reduce risks to an acceptable level
- Monitor the effectiveness of implemented controls
- Review and update risk assessments as needed

# 5.2 Science-Based Quality Risk Management

Determining the risks posed by a computerized system requires a common and shared understanding of:

- Impact of the computerized system on patient safety, product quality, and data integrity
- Supported business processes
- CQAs for systems that monitor or control CPPs
- User requirements
- Regulatory requirements
- Project approach (contracts, methods, timelines)
- System components and architecture
- System functions
- Supplier capability

QRM should be based on scientific knowledge and understanding of the system and its intended use. This enables informed decisions about where to focus effort and resources.

# 5.3 Quality Risk Management Process

The ICH Q9 [14] describes a systematic approach to QRM intended for general application within the pharmaceutical industry. It defines the following two primary principles of QRM:

- "The evaluation of the risk to quality should be based on scientific knowledge and ultimately link to the protection of the patient; and
- The level of effort, formality and documentation of the quality risk-management process should be commensurate with the level of risk."

The QRM process consists of the following steps:

1. **Risk Assessment**: Identifying hazards, analyzing risks, and evaluating their significance
2. **Risk Control**: Implementing measures to reduce risks to an acceptable level
3. **Risk Communication**: Sharing risk information with stakeholders
4. **Risk Review**: Monitoring and reviewing risks and controls over time

## 5.3.1 Initial Risk Assessment

The initial risk assessment provides a high-level understanding of the risks associated with the computerized system. This assessment is used to guide the overall approach to system validation and operation.

## 5.3.2 Functional Risk Assessment

Functional risk assessments are performed for specific system functions or components. These assessments provide detailed information about risks and the controls needed to mitigate them.

## 5.3.3 Risk Control

Risk control involves implementing measures to reduce risks to an acceptable level. Controls may include:

- **Preventive Controls**: Measures to prevent risks from occurring
- **Detective Controls**: Measures to detect when risks have occurred
- **Corrective Controls**: Measures to correct problems when they occur

## 5.3.4 Risk Review

Risk review involves monitoring and reviewing risks and controls over time to ensure they remain effective. This may include:

- **Periodic Reviews**: Regular reviews of risk assessments and controls
- **Incident Reviews**: Reviews triggered by incidents or problems
- **Change Reviews**: Reviews triggered by changes to the system or its environment

---

# 6 Regulated Company Activities

Responsibility for the compliance of computerized systems lies with the regulated company. This involves activities at both the organizational level and at the level of individual systems.

# 6.1 Governance for Achieving Compliance

Achieving robust, cost-effective compliance requires strong governance. Key elements include:

## 6.1.1 Policies and Procedures

Establishing clear policies and procedures for computerized system validation and operation. These should define:

- Requirements for system validation
- Roles and responsibilities
- Documentation requirements
- Change management processes
- Incident management processes

## 6.1.2 Roles and Responsibilities

Identifying clear roles and responsibilities for all individuals involved in computerized system validation and operation. Key roles include:

- **Process Owner**: Responsible for the business process supported by the system
- **System Owner**: Responsible for the technical aspects of the system
- **Quality Assurance**: Responsible for ensuring compliance with quality requirements
- **IT Support**: Responsible for technical support and maintenance

## 6.1.3 Training

Ensuring that all individuals involved in computerized system validation and operation are appropriately trained. Training should cover:

- Regulatory requirements
- Company policies and procedures
- System-specific requirements
- Technical skills

## 6.1.4 Supplier Management

Managing relationships with suppliers to ensure they provide appropriate support for validation and compliance activities. This includes:

- **Supplier Assessment**: Evaluating supplier capability and quality management systems
- **Supplier Audits**: Conducting audits of critical suppliers
- **Supplier Agreements**: Establishing clear agreements with suppliers regarding their responsibilities

## 6.1.5 System Inventory

Maintaining an inventory of all computerized systems to ensure they are properly managed and maintained. The inventory should include:

- System identification and classification
- Validation status
- Maintenance requirements
- Retirement plans

# 6.2 System-Specific Activities

System-specific activities are those performed for individual computerized systems. These activities are scaled based on the risk, complexity, and novelty of the system.

## 6.2.1 Requirements Specification

Defining clear requirements for the computerized system. Requirements should be:

- **Clear and Unambiguous**: Requirements should be written in clear, unambiguous language
- **Testable**: Requirements should be written in a way that allows them to be tested
- **Traceable**: Requirements should be traceable through the system life cycle
- **Risk-Based**: Requirements should focus on aspects that are critical to patient safety, product quality, and data integrity

## 6.2.2 System Design

Designing the system to meet the defined requirements. The design should:

- Address all user requirements
- Incorporate appropriate controls to mitigate identified risks
- Be documented in sufficient detail to support implementation and testing
- Be reviewed and approved by appropriate stakeholders

## 6.2.3 System Implementation

Implementing the system according to the approved design. Implementation activities include:

- **System Installation**: Installing hardware and software components
- **System Configuration**: Configuring the system to meet specifications
- **Custom Development**: Developing custom software components as needed
- **Integration**: Integrating the system with other systems and processes

## 6.2.4 System Testing

Testing the system to verify that it meets requirements and is fit for its intended use. Testing should be:

- **Risk-Based**: Testing effort should be focused on high-risk areas
- **Comprehensive**: Testing should cover all system functions and requirements
- **Documented**: Testing should be documented with clear test procedures and results
- **Independent**: Testing should be performed by individuals independent of system development

## 6.2.5 System Release

Formally releasing the system for operational use. Release activities include:

- **Validation Reporting**: Documenting validation activities and results
- **System Approval**: Obtaining formal approval for system release
- **Handover**: Transferring the system from project to operations
- **Go-Live Activities**: Supporting the transition to operational use

## 6.2.6 System Operation

Operating the system in accordance with defined procedures. Operational activities include:

- **User Training**: Training users on system operation
- **System Monitoring**: Monitoring system performance and availability
- **Incident Management**: Managing incidents and problems
- **Change Management**: Managing changes to the system
- **Maintenance**: Performing routine maintenance activities

## 6.2.7 System Retirement

Retiring the system when it is no longer needed. Retirement activities include:

- **Retirement Planning**: Planning for system retirement
- **Data Migration**: Migrating data to new systems or archives
- **System Decommissioning**: Safely shutting down the system
- **Asset Disposal**: Properly disposing of system assets

---

# 7 Supplier Activities

Although the responsibility for compliance with GxP regulations lies with the regulated company, the supplier may have considerable involvement in the process.

# 7.1 Supplier Products, Applications, and Services

Suppliers provide a range of products, applications, and services for hardware, software, and related technologies including the provision of cloud-computing services.

## 7.1.1 Product Development (GAMP Category 3)

For standard software products, the supplier will normally have developed the product for a general market. The regulated company implements the product, usually with some degree of configuration. The supplier should have procedures in place to ensure that the product is developed and maintained according to good practices.

## 7.1.2 Configured Products (GAMP Category 4)

For configured products, the supplier may be involved in the configuration process. The supplier should have procedures in place to ensure that configuration is performed according to good practices and that the configured system meets the regulated company's requirements.

## 7.1.3 Custom Applications (GAMP Category 5)

For custom applications, the regulated company typically contracts a supplier to develop the application based on defined requirements. The supplier will be involved throughout the full project life cycle and should follow good practices for custom software development.

## 7.1.4 Service Provision

Suppliers that provide IT/IS services (including cloud-computing services) should operate within a quality management system. The required information may be covered by service level agreements or other contractual documents.

# 7.2 Supplier Good Practices

Suppliers should follow good practices throughout the system life cycle. Key practices include:

## 7.2.1 Quality Management System

The supplier should establish and maintain a quality management system that:

- Provides documented procedures and standards
- Ensures activities are performed by competent and trained staff
- Provides evidence of conformance with procedures and standards
- Enables continual improvement

## 7.2.2 Requirements Management

The supplier should ensure that clear requirements are defined and managed throughout the project. Requirements should be:

- Clearly defined and documented
- Reviewed and approved by appropriate stakeholders
- Managed under change control
- Traceable through the system life cycle

## 7.2.3 Design and Development

The supplier should design and develop systems according to good practices. This includes:

- Following established design standards and procedures
- Conducting design reviews
- Managing design changes
- Maintaining traceability between requirements and design

## 7.2.4 Testing

The supplier should test systems thoroughly before release. Testing should:

- Cover all system functions and requirements
- Be performed according to approved test plans
- Be documented with clear test procedures and results
- Include both positive and negative test cases

## 7.2.5 Release Management

The supplier should have formal processes for releasing systems to customers. Release processes should include:

- Defined release criteria
- Formal approval processes
- Release documentation
- Support for customer implementation

## 7.2.6 Support and Maintenance

The supplier should provide ongoing support and maintenance for systems. This includes:

- Technical support for system operation
- Maintenance and updates
- Problem resolution
- Change management

# 7.3 Supplier Assessment

Regulated companies should assess suppliers to ensure they are capable of providing appropriate support for validation and compliance activities. Assessment activities include:

## 7.3.1 Supplier Evaluation

Evaluating potential suppliers based on:

- Technical capability
- Quality management systems
- Experience with similar projects
- Financial stability
- Regulatory compliance experience

## 7.3.2 Supplier Audits

Conducting audits of critical suppliers to verify their capability and quality management systems. Audits should focus on:

- Quality management systems
- Development processes
- Testing practices
- Change management
- Documentation practices

## 7.3.3 Ongoing Monitoring

Monitoring supplier performance throughout the relationship to ensure continued compliance with requirements. This includes:

- Performance reviews
- Periodic reassessments
- Incident management
- Change notifications

---

# 8 Efficiency Improvements

This Guide provides a flexible framework for achieving compliant computerized systems that are fit for their intended use. The benefits will be obtained only if the framework is applied effectively in the context of a particular organization.

Aspects that can assist efficiency include:

- Establishing verifiable and appropriate user requirements
- Making risk-based decisions
- Leveraging supplier input
- Leveraging existing records and information
- Using efficient testing practices
- Employing a well-managed handover process
- Managing changes efficiently
- Anticipating data archiving and migration needs
- Using tools and automation

# 8.1 Establishing Verifiable and Appropriate User Requirements

Clear, verifiable user requirements are fundamental to achieving efficient validation. Requirements should be:

- **Focused on Critical Aspects**: Requirements should focus on aspects that are critical to patient safety, product quality, and data integrity
- **Testable**: Requirements should be written in a way that allows them to be tested objectively
- **Traceable**: Requirements should be traceable through the system life cycle
- **Risk-Based**: The level of detail should be commensurate with the risk associated with the requirement

# 8.2 Making Risk-Based Decisions

Risk-based decision making enables effort to be focused where it is most needed. This includes:

- **Initial Risk Assessment**: Performing initial risk assessments to guide the overall approach
- **Functional Risk Assessment**: Performing detailed risk assessments for specific system functions
- **Risk-Based Testing**: Focusing testing effort on high-risk areas
- **Risk-Based Documentation**: Providing more detailed documentation for high-risk areas

# 8.3 Leveraging Supplier Input

Suppliers can provide valuable input throughout the system life cycle. This includes:

- **Requirements Gathering**: Suppliers can assist with identifying and documenting requirements
- **Risk Assessment**: Suppliers can provide input on technical risks and mitigation strategies
- **Design**: Suppliers can provide design expertise and best practices
- **Testing**: Suppliers can provide testing expertise and existing test documentation
- **Support**: Suppliers can provide ongoing support and maintenance

# 8.4 Leveraging Existing Records and Information

Existing records and information can be leveraged to reduce duplication of effort. This includes:

- **Supplier Documentation**: Using supplier documentation where appropriate
- **Previous Validation**: Building on previous validation activities for similar systems
- **Industry Standards**: Using industry standards and best practices
- **Regulatory Guidance**: Following regulatory guidance and precedents

# 8.5 Using Efficient Testing Practices

Efficient testing practices can reduce the time and effort required for validation. This includes:

- **Risk-Based Testing**: Focusing testing effort on high-risk areas
- **Automated Testing**: Using automated testing tools where appropriate
- **Parallel Testing**: Performing testing activities in parallel where possible
- **Supplier Testing**: Leveraging supplier testing where appropriate

# 8.6 Employing a Well-Managed Handover Process

A well-managed handover process ensures smooth transition from project to operations. This includes:

- **Handover Planning**: Planning the handover process early in the project
- **Documentation**: Ensuring all necessary documentation is available
- **Training**: Providing appropriate training for operational staff
- **Support**: Ensuring appropriate support is available during transition

# 8.7 Managing Changes Efficiently

Efficient change management reduces the impact of changes on validation activities. This includes:

- **Change Control**: Implementing effective change control processes
- **Impact Assessment**: Assessing the impact of changes on validation
- **Risk Assessment**: Assessing the risk associated with changes
- **Regression Testing**: Performing appropriate regression testing

# 8.8 Anticipating Data Archiving and Migration Needs

Planning for data archiving and migration early in the project can reduce future effort. This includes:

- **Data Mapping**: Understanding data structures and relationships
- **Archive Planning**: Planning for data archiving requirements
- **Migration Planning**: Planning for data migration to new systems
- **Retention Requirements**: Understanding regulatory retention requirements

# 8.9 Using Tools and Automation

Tools and automation can improve efficiency and reduce errors. This includes:

- **Validation Tools**: Using tools to support validation activities
- **Testing Tools**: Using automated testing tools
- **Documentation Tools**: Using tools to manage documentation
- **Monitoring Tools**: Using tools to monitor system performance

---

# SELECTED ESSENTIAL APPENDICES

The following appendices have been selected as most valuable for thesis writing and understanding modern GxP compliance approaches:

- **M1**: Validation Planning (fundamental process)
- **M3**: Quality Risk Management (regulatory requirement)
- **M4**: Software/Hardware Categories (system classification)
- **M12**: Critical Thinking (modern compliance approach)
- **D8**: Agile Software Development (contemporary methodology)
- **D11**: AI/ML (emerging technology guidance)
- **S2**: Electronic Production Records (practical implementation)

---

# Appendix M1 - Validation Planning

## 9.1 Introduction

This appendix covers the production of individual validation plans for systems or projects (computerized systems validation plans), and also gives information on validation policies and Validation Master Plans (VMPs) for background and context.

Computerized system validation plans describe how the validation is to be performed for specific systems. Validation policies define management intent and commitment. VMPs describe the areas of the company where validation is required and provides an overview of validation planning for those areas.

It is a regulatory expectation that validation activities are planned; see for example EU Annex 11 [32] Section 4.

## 9.2 Scope

This guidance may be applied to all GxP regulated computerized systems. The guidelines apply to both new and existing computerized systems, and sites and organizations in which these systems are used.

Where a computer system is regarded as one component of a wider manufacturing process or system, particularly in an integrated QbD environment, specific and separate computerized system validation may not be necessary, and separate computerized system validation plans would not be required.

## 9.3 Computerized System Validation Plans

### 9.3.1 General Guidelines

A computerized system validation plan should be produced for each GxP regulated computerized system focusing on aspects related to patient safety, product quality, and data integrity. It should summarize the system and/or project, identify measures for success, and clearly define criteria for final acceptance and release of the system.

The plan should define:
- What activities are required
- How they will be performed and who is responsible
- What the output will be
- What the requirements are for acceptance
- How compliance will be maintained for the lifetime of the system

The level of detail in the plan should reflect the risk, complexity, and novelty of the system.

### 9.3.2 Roles and Responsibilities

Responsibility for computerized system validation planning ultimately rests with the process owner. This may be delegated to a project manager and also may involve the system owner. Typically, the computerized system validation plan is approved by the process owner and quality unit.

### 9.3.3 Contents of the Plan

#### 9.3.3.1 Introduction and Scope
- The scope of the system
- The objectives of the validation process
- Applicable main regulations
- Review, maintenance, or update process for the plan itself

#### 9.3.3.2 System Overview
- Business purpose and intended use for the system
- A description of the system and its data at a high level
- System scope and boundaries and overview of the system architecture

#### 9.3.3.3 Organizational Structure
Roles and responsibilities should be described, including:
- Project manager
- Quality unit
- Process owner and/or system owner
- Subject Matter Experts (SMEs)

#### 9.3.3.4 Quality Risk Management
The QRM approach to be applied should be described, including:
- Initial risk assessment based on business processes
- Overall assessment of system impact
- Stages at which risk assessment will be performed

#### 9.3.3.5 Validation Strategy
The strategy for achieving compliance and ensuring fitness for intended use should describe:
- The life cycle model
- Specification and verification approach
- The inputs and outputs required for each stage
- The acceptance criteria
- Approach to traceability and design review

---

# Appendix M3 - Quality Risk Management

## 11.1 Introduction

This appendix provides further detail on the QRM process introduced in Chapter 5. QRM is a systematic process for the assessment, control, communication, and review of risks to patient safety, product quality, and data integrity, based on a framework consistent with ICH Q9 [14].

## 11.2 Scope

This appendix is applicable to all types of computerized systems used in regulated activities, including those supporting clinical trials, toxicological studies, API production, formulated product production, warehousing, distribution, medical devices, and pharmacovigilance.

## 11.3 Benefits

Application of QRM enables effort to be focused on critical aspects of a computerized system, leading to specific benefits:
- Identification and management of risks to patient safety, product quality, and data integrity
- Scaling of life cycle activities according to system impact and risks
- Better understanding of potential risks and proposed controls
- Supporting regulatory expectations

## 11.4 Roles and Responsibilities

| Role | Responsibilities |
|------|------------------|
| Process Owner/System Owner | Establish team and provide resources, participate in risk assessments, approve documentation |
| SME Team | Identify, analyze, and evaluate risks; develop controls |
| Quality Unit | Identify compliance-related risks, participate in assessments, approve documentation |
| Supplier | Provide product information, participate in risk assessments, provide advice on controls |

## 11.5 Guidance

### 11.5.1 Scalability of the Process

The five-step risk management process may be scaled according to risk, complexity, and novelty of individual system, with each step building upon the previous output.

### 11.5.2 Applying Risk Management Based on the Business Process

To effectively apply QRM to computerized systems, it is important to have a thorough understanding of the business process supported by the computerized systems. Key considerations include:

- **What are the hazards?** Understanding what could go wrong with the system
- **What is the harm?** Identifying potential consequences of hazards
- **What is the impact?** Estimating possible consequences on patient safety, product quality, and data integrity
- **What is the probability of failure?** Understanding likelihood of failure occurrence

---

# Appendix M4 - Categories of Software and Hardware

## 12.1 Introduction

This appendix provides guidance on the categorization of software and hardware used in computerized systems. The categorization is used to determine the appropriate level of effort for verification and validation activities.

## 12.2 Software Categories

### GAMP Category 1: Infrastructure Software
- Operating systems, database engines, programming languages
- Generally not configured and used as supplied
- Verification focused on installation and operational procedures

### GAMP Category 3: Non-Configured Products
- Commercial off-the-shelf software packages
- Used without modification or configuration
- Verification focused on installation and operational procedures

### GAMP Category 4: Configured Products
- Commercial software packages requiring configuration
- Configuration parameters define system behavior
- Verification includes both product testing and configuration verification

### GAMP Category 5: Custom Applications
- Software developed specifically for a particular application
- Requires full development life cycle approach
- Comprehensive specification and verification activities required

## 12.3 Hardware Categories

### GAMP Category 1: Established Hardware
- Standard computer hardware components
- Well-established and proven technology
- Verification focused on installation and operational procedures

### GAMP Category 2: Firmware Hardware
- Hardware with embedded firmware
- Firmware may require verification depending on complexity
- Focus on operational procedures and interface verification

## 12.4 Application to Validation

The categorization helps determine:
- Level of supplier assessment required
- Extent of specification required
- Level of verification testing needed
- Documentation requirements

---

# Appendix M12 - Critical Thinking

## 20.1 Introduction

Critical thinking is the objective analysis and evaluation of an issue in order to form a judgment. It is the intellectually disciplined process of actively and skillfully conceptualizing, applying, analyzing, synthesizing, and/or evaluating information gathered from, or generated by, observation, experience, reflection, reasoning, or communication, as a guide to belief and action.

## 20.2 Application to GAMP

Critical thinking should be applied throughout the computerized system life cycle to:
- Determine appropriate levels of effort for life cycle activities
- Identify and assess risks effectively
- Make informed decisions about control strategies
- Evaluate the effectiveness of implemented controls
- Ensure systems remain fit for their intended use

## 20.3 Critical Thinking Framework

### 20.3.1 Question Everything
- Challenge assumptions and conventional wisdom
- Ask "why" and "what if" questions
- Consider alternative approaches and solutions

### 20.3.2 Gather Information
- Collect relevant data from multiple sources
- Verify information accuracy and currency
- Consider the context and limitations of information

### 20.3.3 Analyze and Evaluate
- Examine information objectively
- Identify patterns, relationships, and contradictions
- Consider multiple perspectives and viewpoints

### 20.3.4 Draw Conclusions
- Base conclusions on evidence and logical reasoning
- Acknowledge uncertainty and limitations
- Be prepared to revise conclusions with new information

## 20.4 Benefits of Critical Thinking

- **Improved Decision Making**: Better informed and more rational decisions
- **Risk Management**: More effective identification and mitigation of risks
- **Resource Optimization**: More efficient use of validation resources
- **Regulatory Compliance**: Better alignment with regulatory expectations
- **Continuous Improvement**: Enhanced ability to learn and adapt

---

# Appendix D8 - Agile Software Development

## 28.1 Introduction

Agile software development is an iterative and incremental approach to software development that emphasizes flexibility, collaboration, and customer satisfaction. This appendix provides guidance on applying GAMP principles to Agile development methodologies.

## 28.2 Agile Principles

### 28.2.1 Core Values
- **Individuals and interactions** over processes and tools
- **Working software** over comprehensive documentation
- **Customer collaboration** over contract negotiation
- **Responding to change** over following a plan

### 28.2.2 Key Practices
- **Iterative Development**: Software developed in short iterations (sprints)
- **Continuous Integration**: Frequent integration of code changes
- **Test-Driven Development**: Tests written before code
- **Continuous Delivery**: Frequent deployment of working software

## 28.3 GAMP and Agile Alignment

### 28.3.1 Specification and Verification
- **User Stories**: Replace traditional requirements documents
- **Acceptance Criteria**: Define testable conditions for user stories
- **Sprint Reviews**: Provide continuous verification of functionality
- **Retrospectives**: Enable continuous improvement

### 28.3.2 Documentation
- **Living Documentation**: Documentation that evolves with the system
- **Just Enough Documentation**: Focus on essential documentation
- **Automated Documentation**: Generated from code and tests
- **Working Software**: Primary measure of progress

## 28.4 Risk Management in Agile

### 28.4.1 Continuous Risk Assessment
- Risk assessment performed at start of each sprint
- Risks identified and addressed incrementally
- Risk register maintained throughout development

### 28.4.2 Risk Mitigation
- **Short Iterations**: Reduce risk through early feedback
- **Continuous Testing**: Identify issues early
- **Frequent Reviews**: Ensure alignment with requirements

## 28.5 Validation Considerations

### 28.5.1 Validation Planning
- **Agile Validation Plan**: Adapted for iterative development
- **Definition of Done**: Clear criteria for completion
- **Minimum Viable Product**: Initial version with core functionality

### 28.5.2 Testing Strategy
- **Automated Testing**: Regression testing for each iteration
- **Continuous Integration**: Automated build and test processes
- **User Acceptance Testing**: Continuous validation with users

---

# Appendix D11 - Artificial Intelligence and Machine Learning

## 31.1 Introduction

AI/ML systems present unique challenges for GxP validation due to their ability to learn and adapt. This appendix provides guidance on applying GAMP principles to AI/ML systems.

## 31.2 AI/ML System Types

### 31.2.1 Static Machine Learning Systems
- **Pre-trained Models**: Models trained before deployment
- **Fixed Parameters**: No learning during operation
- **Validation Approach**: Similar to traditional software with focus on model performance

### 31.2.2 Dynamic Machine Learning Systems
- **Online Learning**: Models that continue learning during operation
- **Adaptive Parameters**: Parameters change based on new data
- **Validation Approach**: Continuous monitoring and validation required

## 31.3 Validation Considerations

### 31.3.1 Data Quality
- **Training Data**: Quality and representativeness of training data
- **Data Governance**: Processes for data collection, storage, and management
- **Bias Detection**: Identification and mitigation of data bias

### 31.3.2 Model Performance
- **Performance Metrics**: Accuracy, precision, recall, F1-score
- **Validation Data**: Independent data for model validation
- **Cross-Validation**: Multiple validation approaches

### 31.3.3 Model Interpretability
- **Explainable AI**: Understanding model decision-making
- **Feature Importance**: Identifying key input variables
- **Model Transparency**: Documentation of model architecture and logic

## 31.4 Risk Management

### 31.4.1 Unique Risks
- **Model Drift**: Performance degradation over time
- **Data Drift**: Changes in input data distribution
- **Adversarial Attacks**: Malicious manipulation of inputs

### 31.4.2 Risk Mitigation
- **Continuous Monitoring**: Real-time performance monitoring
- **Model Retraining**: Regular updates with new data
- **Robust Testing**: Comprehensive testing including edge cases

## 31.5 Ongoing Validation

### 31.5.1 Continuous Validation
- **Performance Monitoring**: Ongoing assessment of model performance
- **Alert Systems**: Automated alerts for performance degradation
- **Validation Schedule**: Regular re-validation activities

### 31.5.2 Change Management
- **Model Updates**: Controlled process for model changes
- **Version Control**: Tracking of model versions and changes
- **Impact Assessment**: Evaluation of change impact on validation

---

# Appendix S2 - Electronic Production Records

## 47.1 Introduction

Electronic Production Records (EPRs) are digital records that capture and store information related to the production of pharmaceutical products. This appendix provides guidance on the validation and management of EPR systems.

## 47.2 EPR System Components

### 47.2.1 Data Collection
- **Automated Data Capture**: Direct interface with manufacturing equipment
- **Manual Data Entry**: User interface for manual data input
- **Data Validation**: Real-time validation of entered data

### 47.2.2 Data Storage
- **Database Management**: Secure storage of production data
- **Data Integrity**: Measures to ensure data accuracy and completeness
- **Backup and Recovery**: Protection against data loss

### 47.2.3 Data Processing
- **Calculations**: Automated calculations and derived values
- **Approvals**: Electronic signature and approval workflows
- **Reporting**: Generation of production reports and summaries

## 47.3 Validation Approach

### 47.3.1 Data Integrity
- **ALCOA+ Principles**: Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, Available
- **Audit Trails**: Complete record of data changes and access
- **Electronic Signatures**: Secure authentication and authorization

### 47.3.2 System Validation
- **Functional Testing**: Verification of system functionality
- **Integration Testing**: Testing of interfaces with other systems
- **Performance Testing**: Validation of system performance under load

### 47.3.3 Operational Validation
- **User Training**: Comprehensive training for system users
- **Operational Procedures**: Standard operating procedures for system use
- **Periodic Review**: Regular assessment of system performance

## 47.4 Data Life Cycle Management

### 47.4.1 Data Creation
- **Data Standards**: Standardized formats and structures
- **Data Validation**: Real-time validation during data entry
- **Version Control**: Management of data versions and changes

### 47.4.2 Data Use
- **Access Control**: Appropriate user permissions and restrictions
- **Data Retrieval**: Efficient methods for data access and retrieval
- **Data Analysis**: Tools and methods for data analysis

### 47.4.3 Data Retention
- **Retention Periods**: Compliance with regulatory retention requirements
- **Archive Systems**: Long-term storage of production records
- **Data Migration**: Transfer of data to new systems or formats

## 47.5 Compliance Considerations

### 47.5.1 Regulatory Requirements
- **FDA 21 CFR Part 11**: Electronic records and signatures
- **EU Annex 11**: Computerized systems validation
- **ICH Q7**: Good manufacturing practice for APIs

### 47.5.2 Quality Management
- **Change Control**: Controlled process for system changes
- **Incident Management**: Response to system issues and failures
- **Continuous Improvement**: Ongoing enhancement of system capabilities

---

# Essential Glossary Terms

**Artificial Intelligence (AI)**: The simulation of human intelligence processes by machines, especially computer systems.

**Critical Quality Attribute (CQA)**: A physical, chemical, biological or microbiological property that should be within an appropriate limit to ensure desired product quality.

**Critical Process Parameter (CPP)**: A process parameter whose variability has an impact on a CQA and should be monitored or controlled.

**Electronic Production Record (EPR)**: A record that stores data and information from production-related activities created by systems during execution.

**Machine Learning (ML)**: A subset of AI that enables systems to learn and improve from experience without being explicitly programmed.

**Quality by Design (QbD)**: A systematic approach to development emphasizing product and process understanding and process control.

**Quality Risk Management (QRM)**: A systematic process for assessment, control, communication and review of risks to quality.

**Subject Matter Expert (SME)**: An individual with specific expertise in a particular area or topic.

**Validation Master Plan (VMP)**: A high-level document that establishes an umbrella validation plan for the entire project.

---

**For complete document citation:**
ISPE. (2022). *GAMP® 5 Guide: A Risk-Based Approach to Compliant GxP Computerized Systems* (2nd ed.). International Society for Pharmaceutical Engineering.

**Document Status:** Truncated version preserving essential content for thesis research - original 900KB document reduced to ~400KB while maintaining core regulatory guidance and modern compliance approaches.