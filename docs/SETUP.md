# Owner setup and YouTube verification

Current as of 2026-09-09. [Recovery and next steps](RECOVERY_AND_NEXT_STEPS.md) is the complete handoff.

## The action needed now: custom-thumbnail phone verification

1. Sign into YouTube with the account used for the review. In the profile menu, choose channel **Andreas Döpfert / @Papa_baer_andreas** (`UC3yza3Tcu5vyNwr661Uai6g`). ErklaerBaer is currently the video brand, not the channel display name.
2. Open [youtube.com/verify](https://www.youtube.com/verify). Alternatively use YouTube Studio → Einstellungen → Kanal → Verfügbarkeit von Funktionen and open the phone/intermediate-feature verification.
3. Choose your country and **SMS** or **voice call**, enter your phone number and request the code.
4. Enter the code directly on YouTube and complete verification. Do not send the code or number in chat.
5. Return to [the existing video](https://studio.youtube.com/video/z_1Fx6L3N_Q/edit), refresh, and check that **Thumbnail → Datei hochladen** no longer asks for phone verification. Tell the agent verification is complete; it can apply the prepared thumbnail to this same Private video.

Google receives your number to deliver the verification code. Phone verification unlocks custom thumbnails; ID/video verification is part of separate advanced-feature access and is not the step needed for this thumbnail. If SMS does not arrive after a few minutes, try the voice-call option. A phone number can verify at most two channels per year. Source checked 2026-09-09: [YouTube account verification help](https://support.google.com/youtube/answer/171664?hl=en).

The Private review is already watchable without this step: https://youtu.be/z_1Fx6L3N_Q.
Prepared thumbnail: `artifacts/review-v3/guitar/cedfada8807f70f3fe6b4a2c/thumbnail.jpg`.

## Already complete — do not repeat

- Google Cloud API and existing service-account prediction access; Gemini synthesis succeeded.
- Native v3 Rive embedded `.rev` backup and `.riv` runtime export; six-action baking and QA succeeded.
- Chrome extension Allow access to file URLs; video and captions uploaded successfully.
- Private YouTube review save, Dutch captions, made-for-kids setting and disabled notifications.

## Later gates

Full creative acceptance is pending. Native guitar prop Rive sources/runtime remain unfinished. Coin/safari follow guitar acceptance. No production scheduler or public release is active.
YouTube API refresh-token setup, Nochmal feed deployment/read-token setup and weekly activation are later, separately authorized work. They are not required for the current browser-based review or phone verification.
Do not paste credentials into chat or restore old daily instructions. Historical onboarding is preserved under `archive/2026-09-09-before-recovery-consolidation/docs/SETUP.md`.
