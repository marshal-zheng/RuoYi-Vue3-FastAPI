import type { ZxFeedbackApi, ZxMessageParams } from '@zxio/zxui';
import { createFeedbackChannel } from './channel';

type MessageSender = ZxFeedbackApi['message'];
type MessageResult = Awaited<ReturnType<MessageSender>>;

const channel = createFeedbackChannel<ZxMessageParams, MessageResult>();
export const showMessage = channel.send;
export const bindMessageFeedback = channel.bind;
