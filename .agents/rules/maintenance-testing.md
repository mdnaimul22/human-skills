---
trigger: always_on
name: maintenance_testing
description: Guidelines for Security, Refactoring, and Verification.
---

# Maintenance & Testing

## 1. Security-Safety Practices
> *"Security is a first-class citizen, not an afterthought."*  
> **With Comprehensive test coverage that is maintained continuously**

| Risk | Mitigation Strategy |
| :--- | :--- |
| **Injection Attacks (SQL/Command/Shell)** | Never concatenate user input directly into executable strings. Always use Parameterized queries, ORM, or Safe execution APIs. |
| **Path Traversal** | When accessing the file system, sanitize any user-provided path inputs and strictly enforce sandbox boundaries to block access outside permitted directories. |
| **Secret Leakage** | Never hardcode API Keys or Credentials in the source code. Always use Environment Variables (`.env`) or a Secret Manager. |
| **Rate Limiting & Abuse** | Enforce request rate sizing limit restrictions and payload thresholds on all public/external APIs. |
| **Failover & Stability** | Implement Error Retry Logic with Exponential Backoff to prevent system crashes triggered by network failures during third-party or external API calls. |

---

## 2. Advanced Refactoring & Code Evolution
> *"Refactoring is a deliberate process, not a quick fix."*

**Zero Behavior Changes Verified** — The primary goal of refactoring is to significantly reduce complexity and consistently ensure safety, but the behavior of existing code must never be broken under any circumstances.

### 2.1 The Master Refactoring Strategy

> [!IMPORTANT]  
> **Method Extraction & Clean-up:** Long method decomposition • Complex conditional extraction • Loop body extraction • Duplicate code consolidation • Guard clause introduction • Command query separation.

- **Design Pattern Application:** Apply `Strategy`, `Factory`, `Observer`, or `Decorator` patterns. Eliminate hardcoded if-else or switch/case logic using *Replace Conditional with Polymorphism* or *Replace Type Code with Subclasses*.
- **API & Database Optimization:** 
  - **API:** Ensure Endpoint consolidation, Error handling standardization, Versioning strategy, and firmly maintain backward compatibility.
  - **Database:** Boost performance using Query simplification, Schema normalization, Index optimization, and Caching strategies (Lazy evaluation).
- **Architectural Refactoring:** Break tight-coupling using Interface segregation and Dependency inversion (*Replace Inheritance with Delegation*, *Extract Interface*). Consider separate Service extraction or Event-driven refactoring if required.
- **Safety First:** At the end of the refactoring process, validate utilizing Regression detection and Coverage analysis to ensure that the initial functionality works exactly as prior.

---

## 3. Verification & Testing

Testing is mandatory not just for finding bugs in the code, but for keeping the codebase production-ready and future-proof. The following verification strategies must be applied throughout the project lifecycle:

- **Golden Master / Approval Testing:** When refactoring legacy code or validating complex outputs, save the current behavior as a "Golden Record". Ensure that the new output maps exactly identically post-refactoring.
- **Mutation Testing:** To verify the actual robustness of the unit tests you have written, introduce deliberate bugs (Mutants) into the main code and see if the tests fail. 100% coverage does not equate to safety; having robust assertions is far more critical.
- **Performance Testing:** Validate whether the system design is genuinely ultra-fast. Measure if I/O bound operations during loads are triggering blocking issues.
- **Characterization Tests:** Execute these tests to comprehend the undocumented behaviors of any library or third-party API so your system does not break if the API updates in the future.
- **Integration Validation:** Validate that end-to-end data flow operates perfectly when different modules — specifically the `services/`, `providers/`, and `database` layers — interact simultaneously.
- **Memory Optimization & Resource Pooling:** Ensure proper connection pooling for database or external API calls. Maintain resource cleanup (e.g., using `finally` blocks or `async with` context managers) to prevent memory leaks and slower responses.
