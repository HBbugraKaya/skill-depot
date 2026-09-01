# Java Mentoring Guide

Use this guide when the learner is working with Java, Maven or Gradle, JUnit,
Spring, or Spring Boot. Apply it together with the main mentoring method rather
than as a separate checklist.

## Establish the Java context

Before recommending syntax or APIs, inspect what is available:

- `pom.xml`, `build.gradle`, or `build.gradle.kts`;
- the configured Java release and installed toolchain;
- framework and dependency versions;
- nearby code, tests, and established conventions;
- the exact compiler error, stack trace, failing assertion, or unexpected
  behavior.

Use Java 21 as the default baseline unless the user explicitly requires older
compatibility. Do not recommend an API from memory when compatibility matters;
verify it against the project's version or official documentation.

Identify which kind of problem is present:

- **Compilation:** syntax, types, generics, method resolution, visibility, or
  missing dependencies.
- **Runtime:** an exception, invalid state, resource failure, or concurrency
  behavior.
- **Test:** incorrect production behavior, incorrect expectation, or unsuitable
  test setup.
- **Spring startup:** bean creation, dependency injection, configuration,
  mapping, persistence metadata, or environment settings.
- **Behavioral:** the program runs but produces the wrong result.

This classification keeps the learner from changing code before understanding
what kind of evidence the tool is providing.

## Teach Java through its execution model

Connect syntax to the behavior it creates. Depending on the current problem,
make the relevant relationship explicit:

- source code is compiled to bytecode and executed by the JVM;
- variables hold primitive values or references, not objects themselves;
- object identity (`==`) and logical equality (`equals`) answer different
  questions;
- generic types provide compile-time constraints and are subject to type
  erasure;
- exceptions unwind the call stack until a compatible handler is found;
- collections differ in ordering, uniqueness, lookup behavior, and mutability;
- streams describe a data-processing pipeline and execute when a terminal
  operation runs;
- threads share heap state, so correctness depends on ownership, visibility,
  and synchronization.

Teach only the part needed for the current task. Connect later concepts to those
the learner has already demonstrated rather than restarting from first
principles.

## Prefer modern Java when it clarifies intent

Modern Java is the default when the project supports it and the feature makes
the code easier to understand. It is not a quota.

### Records

Prefer a record for a simple immutable data carrier whose meaning is represented
by its components, such as:

- request and response DTOs;
- projections;
- commands, events, and small value carriers;
- configuration data supported by the framework version.

A record automatically supplies a canonical constructor, component accessors,
and value-based `equals`, `hashCode`, and `toString`. Explain this the first time
the learner sees one so the shorter code does not hide behavior from them.

Do not force a record onto a type that needs mutable lifecycle state, framework
proxy behavior, inheritance, or identity independent of its fields. In
particular, keep JPA entities as conventional classes unless the persistence
model and provider explicitly support a different design.

Example teaching response:

> This request object only carries validated input and should not change after
> creation. A record expresses that contract directly:
>
> ```java
> public record RegistrationRequest(
>         @NotBlank String firstName,
>         @NotBlank String lastName) {
> }
> ```
>
> `firstName` and `lastName` become final components, and Java generates the
> constructor and accessors. We are choosing a record because this is an
> immutable boundary value, not simply because records are newer. Check the
> service next: does it only read this request, or is anything trying to mutate
> it?

### Optional

Prefer `Optional<T>` as a return type when absence is a normal, meaningful
outcome and the caller must decide what that absence means. Repository lookup
methods are a common example.

Do not use `Optional` mechanically:

- do not return `null` instead of `Optional.empty()`;
- normally avoid it for fields, method parameters, record components, and JPA
  entity attributes;
- return an empty collection rather than `Optional<List<T>>` when “no elements”
  already represents absence;
- avoid `get()` without a prior proof that a value exists;
- use `map`, `flatMap`, `orElseThrow`, `ifPresent`, or another operation that
  states the intended behavior;
- explain the eager evaluation of `orElse` versus the lazy evaluation of
  `orElseGet` when it affects behavior or cost.

Example teaching response:

> A username lookup can legitimately find no trainer, so the repository can
> make that possibility visible with `Optional<Trainer>`. At the service
> boundary, absence becomes a domain decision:
>
> ```java
> return trainerRepository.findByUsername(username)
>         .orElseThrow(() -> new EntityNotFoundException("Trainer not found"));
> ```
>
> This does not use `Optional` to eliminate every possible `null`. It uses it at
> the one boundary where “found or not found” is part of the method's contract.

### Other modern features

Use these when they improve the local expression:

- switch expressions for value-producing branches;
- pattern matching when it removes a redundant cast or clarifies type-based
  behavior;
- text blocks for genuinely multiline text;
- `var` for local variables when the assigned expression makes the type
  obvious;
- streams for clear transformations, filtering, grouping, and aggregation;
- ordinary loops when control flow, mutation, early exit, or debugging would be
  clearer;
- virtual threads for suitable high-concurrency blocking I/O workloads, not as
  a decorative replacement for every thread or executor.

Always teach the semantic change, not merely the shorter syntax.

## Read Java errors with the learner

### Compiler errors

Start with the first relevant compiler error; later messages may be cascading
effects. Translate it into plain language:

1. What type or symbol did the compiler expect?
2. What did it actually receive or fail to find?
3. Which expression created the mismatch?
4. What is the smallest change that makes the contract consistent?

Do not propose casts, raw types, or suppressed warnings merely to silence the
compiler. They often remove useful evidence without fixing the model.

### Stack traces

Read a stack trace in this order:

1. Exception type and message.
2. The first relevant frame in application code.
3. The caller chain needed to understand how execution reached that frame.
4. Each meaningful `Caused by` section, from the most specific cause outward.

Example:

> The final line is not automatically the root cause. Here,
> `BeanCreationException` describes Spring's failure, while the nested
> `Caused by: MappingException` explains why creation failed. Find the deepest
> cause that still describes this failure, then locate the first frame or
> configuration entry owned by the application.

For a `NullPointerException`, identify the expression that was null and trace
which contract allowed it. Do not add a null check until the learner knows
whether null is valid, invalid, or a missing-data signal that should be modeled
differently.

### Failing tests

Separate three possibilities:

- production behavior violates the requirement;
- the assertion describes the wrong requirement;
- setup or mocks do not represent the real collaboration.

Have the learner state the behavior in one sentence before changing either the
test or production code.

## Teach exceptions as boundary decisions

Explain checked and unchecked exceptions before asking the learner to choose:

- a checked exception is part of the compile-time method contract and callers
  must handle or declare it;
- an unchecked exception can propagate without a `throws` declaration and is
  often appropriate for programming errors or application rules handled at a
  higher boundary.

Catch an exception only where the code can recover, add meaningful context, or
translate it for another boundary. Do not catch merely to log and rethrow. Avoid
large custom exception hierarchies unless the application has distinct handling
behavior that justifies them.

## Apply Spring Boot proportionally

When Spring Boot is involved, also apply the `learn-spring-boot` skill. Preserve
these teaching defaults:

- explain what Spring Boot supplies through convention before adding explicit
  configuration;
- use constructor injection and immutable dependency fields;
- keep controllers focused on HTTP concerns and place real business rules in
  the behavior that owns them;
- use DTOs where an external boundary needs its own contract, often as records;
- validate input at the earliest trustworthy boundary without duplicating the
  same checks through every layer;
- use transactions around a real unit of work, not on every method by habit;
- prefer readable Spring Data derived queries before custom query machinery;
- centralize HTTP exception translation when multiple endpoints benefit from a
  consistent response;
- avoid interfaces, mappers, wrappers, configuration beans, and layers that
  exist only to look “enterprise.”

Teach annotations by their runtime role. For example, do not stop at
“`@Valid` enables validation”; show that Spring validates the deserialized
request before the controller method proceeds and routes a failure through its
MVC exception handling.

When a Spring component represents a foundational framework boundary, explain
the caller, the contract it fulfills, the relevant runtime sequence, and the
responsibilities that remain elsewhere. Verify how the current framework
configuration realizes that flow; do not turn one example from the learner's
project into a permanent curriculum requirement.

## Test at the lightest useful level

Use JUnit 5 and choose the smallest test that proves the current behavior:

- a plain unit test for domain or service logic that needs no Spring context;
- Mockito only for real collaborators at the unit boundary;
- `@WebMvcTest` for the MVC contract;
- `@DataJpaTest` for persistence mappings and queries;
- `@SpringBootTest` when interaction across the application context is the
  behavior under test;
- parameterized tests when multiple inputs exercise the same rule.

Assert observable behavior. Do not test generated accessors, framework
implementation details, or mock interactions when the resulting behavior
already proves the collaboration.

When showing Red–Green–Refactor, keep each increment small enough that the
learner can explain why the test fails, why the minimum change passes, and what
the refactor improves without changing behavior.

## Reinforce durable Java understanding

Use later tasks to revisit concepts naturally:

- connect a record DTO to immutability and value equality;
- connect `Optional` to explicit absence and API contracts;
- connect a stack trace to call-stack unwinding;
- connect a transaction failure to exception propagation;
- connect a failing collection test to equality and hashing;
- connect a Spring bean error to object construction and dependency graphs.

Do not mark these concepts as mastered after one explanation. Look for transfer:
can the learner recognize and apply the same idea in a different class or
problem?

