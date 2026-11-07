# Repository Access and Branch Protection

This file describes the intended controls for `Master-Chiken/SW_RACER_RE`. It is a setup checklist, not proof that GitHub settings have already been enabled.

## The operating model

The default rule is **contribute freely, integrate centrally**:

- **Project Owner (@Master-Chiken):** retains repository administration and is the only person who should merge pull requests into the official default branch.
- **Contributors:** can implement complete features, conduct reverse-engineering research, write tests, improve tooling, and submit substantial pull requests from their own forks. They do not need write access to the official repository to do meaningful work.
- **Trusted collaborators with direct write access:** GitHub personal repositories grant collaborators broad write access. Depending on branch rules, they may be able to push branches and merge approved pull requests. Do not grant this access if strict owner-only merging is required.
- **Public contributors:** can fork this public repository and propose changes through a pull request. A pull request is a proposal; nothing enters the official branch until the owner merges it.

**Important limitation:** on a personal-account repository, collaborator permissions are not granular enough to safely treat a write collaborator as “can push feature branches but can never merge.” If owner-only merging is a firm requirement, keep direct write access limited to the owner and have other contributors work through forks.

## GitHub configuration checklist

Open [Settings → Branches](https://github.com/Master-Chiken/SW_RACER_RE/settings/branches) in the repository. Create a branch protection rule for the actual default branch (`master` at the time these instructions were written, unless it has since been renamed) or create an active branch ruleset targeting the default branch.

Configure:

- [ ] Require a pull request before merging.
- [ ] Require at least 1 approving review.
- [ ] Require review from Code Owners.
- [ ] Dismiss stale pull request approvals when new commits are pushed.
- [ ] Require conversation resolution before merging.
- [ ] Block force pushes.
- [ ] Block branch deletion.
- [ ] Do not add contributors or apps to a bypass list for the default branch.
- [ ] Do not enable options that let contributors bypass required pull requests or reviews.
- [ ] Keep repository administration with the Project Owner.
- [ ] Disable auto-merge if you want the owner to make an explicit final merge decision each time.
- [ ] Keep direct write access restricted to the owner if only the owner must be able to merge.

The existing `.github/CODEOWNERS` file names `@Master-Chiken` as owner of all paths, including the CODEOWNERS file itself. GitHub must have required Code Owner review enabled for that designation to become a merge requirement.

Branch protection can require the owner's approval, but on a personal repository it does not turn a write collaborator into a “push-only” role. For a strict owner-only merge workflow, the most reliable practical approach is to have contributors work from forks and not grant them direct write access.

## How to work with a contributor

1. Agree on the task's outcome, boundaries, and evidence needed; use a GitHub issue or a written task description.
2. Have the contributor create a branch in their own fork and submit a pull request against the official default branch.
3. Review the implementation, test evidence, scope, generated files, and any copyright concerns.
4. Request specific changes where needed. The contributor can continue iterating on their fork.
5. Merge the pull request yourself only when it is ready.
6. Credit the contributor in the pull request history and release notes where appropriate.

## Important limitations

GitHub cannot stop people from cloning or forking a public repository. It can stop them from writing to this repository directly. Public users may still propose pull requests; proposals do not change the official branch unless merged. Never put passwords, tokens, secrets, original commercial game executables, or third-party proprietary assets in the repository.

If the project later needs separate fine-grained roles for developers, testers, triagers, and maintainers, consider an organisation-owned repository before transferring anything. Do not transfer the repository merely to solve this immediate problem; first establish a reliable fork-and-pull-request workflow.
