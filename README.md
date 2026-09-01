# Skill Depot

Personal Cursor Agent Skills collection.

## Skills

| Skill | Description |
|-------|-------------|
| [adaptive-java-backend-tutor](skills/adaptive-java-backend-tutor/) | Adaptive tutor for Java 21+, Spring Boot, and backend engineering |
| [comprehensive-repository-review](skills/comprehensive-repository-review/) | Independent architecture, security, and code review workflow |
| [find-skills](skills/find-skills/) | Discover and install agent skills |
| [java-junit](skills/java-junit/) | JUnit 5 unit testing best practices |
| [java-springboot](skills/java-springboot/) | Spring Boot development best practices |
| [learn-spring-boot](skills/learn-spring-boot/) | Spring Boot learning mentor with pragmatic explanations |
| [mentoring-juniors](skills/mentoring-juniors/) | Socratic mentoring for junior developers |
| [study](skills/study/) | Structured study and learning workflows |

## Install

Copy any skill folder into your personal skills directory:

```bash
# Cursor personal skills
cp -r skills/<skill-name> ~/.cursor/skills/

# Or agents skills path
cp -r skills/<skill-name> ~/.agents/skills/
```

On Windows (PowerShell):

```powershell
Copy-Item -Recurse skills\<skill-name> $env:USERPROFILE\.cursor\skills\
```

## Usage

Skills with `disable-model-invocation: true` load only when explicitly referenced in chat.
Others may auto-invoke based on their description triggers.

Example:

```
Use the comprehensive-repository-review skill to review this repository.
```

## Sources

- `adaptive-java-backend-tutor` — from [gym-crm](https://github.com/HBbugraKaya/gym-crm)
- Other skills — personal Cursor skills collection
