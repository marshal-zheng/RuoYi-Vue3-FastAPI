import type { ZxFeedbackApi, ZxNotificationParams } from '@zxio/zxui';
import { createFeedbackChannel } from './channel';

type NotificationResult = Awaited<ReturnType<ZxFeedbackApi['notification']>>;
const channel = createFeedbackChannel<ZxNotificationParams, NotificationResult>();
export const showNotification = channel.send;
export const bindNotificationFeedback = channel.bind;
