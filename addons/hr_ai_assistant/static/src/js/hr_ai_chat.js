/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class HRAIChatWidget extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            messages: [],
            input: "",
            loading: false,
        });
        this.chatContainer = useRef("chatContainer");

        onMounted(async () => {
            await this.loadHistory();
            if (this.state.messages.length === 0) {
                this.addWelcomeMessage();
            }
        });
    }

    addWelcomeMessage() {
        this.state.messages.push({
            message: "🤖 Xin chào! Tôi là HR AI Assistant.\n\nTôi có thể giúp bạn:\n• Tra cứu thông tin nhân viên\n• Xem lương và bảo hiểm\n• Kiểm tra chấm công và nghỉ phép\n• Thống kê đi muộn, về sớm\n\nHãy thử hỏi tôi nhé!",
            is_bot: true,
            time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        });
    }

    async loadHistory() {
        try {
            const result = await this.rpc("/hr_assistant/get_history", {});
            if (result.success) {
                this.state.messages = result.messages;
                this.scrollToBottom();
            }
        } catch (error) {
            console.error("Error loading history:", error);
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            if (this.chatContainer.el) {
                this.chatContainer.el.scrollTop = this.chatContainer.el.scrollHeight;
            }
        }, 100);
    }

    async sendMessage() {
        const message = this.state.input.trim();
        if (!message || this.state.loading) return;

        this.state.input = "";
        this.state.loading = true;

        try {
            const result = await this.rpc("/hr_assistant/send_message", {
                message: message,
            });

            if (result.success) {
                this.state.messages.push(result.data.user_message);
                this.state.messages.push(result.data.bot_message);
                this.scrollToBottom();
            }
        } catch (error) {
            this.state.messages.push({
                message: "❌ Lỗi kết nối: " + error.message,
                is_bot: true,
                time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
            });
        } finally {
            this.state.loading = false;
        }
    }

    onKeyPress(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    askSample(question) {
        this.state.input = question;
        this.sendMessage();
    }

    async clearHistory() {
        if (confirm("Bạn có chắc muốn xóa toàn bộ lịch sử chat?")) {
            try {
                await this.rpc("/hr_assistant/clear_history", {});
                this.state.messages = [];
                this.addWelcomeMessage();
            } catch (error) {
                alert("Lỗi khi xóa lịch sử: " + error.message);
            }
        }
    }

    formatMessage(text) {
        // Convert \n to <br> for display
        return text.replace(/\n/g, '<br/>');
    }
}

HRAIChatWidget.template = "hr_ai_assistant.ChatWidget";

registry.category("actions").add("hr_ai_chat_widget", HRAIChatWidget);
