"""
RAG增强版调度器 - 展示如何真正集成RAG系统
这个文件展示了如何让RAG系统基于用户问题进行智能检索，而不仅仅是标签匹配
新增：连续对话功能支持
"""

import time
import threading
from datetime import datetime
from notion_handler import NotionHandler
from llm_handler import LLMHandler
from template_manager import TemplateManager
from conversation_manager import ConversationManager

class RAGEnhancedScheduler:
    """RAG增强版消息处理调度器"""
    
    def __init__(self, config, gui=None):
        self.config = config
        self.gui = gui
        self.is_running = False
        
        # 初始化处理器
        self.notion_handler = NotionHandler(config)
        self.llm_handler = LLMHandler(config["openrouter"]["api_key"])
        self.template_manager = TemplateManager()
        
        # 初始化连续对话管理器
        self.conversation_manager = ConversationManager(self.notion_handler, config)
        
        # 统计信息
        self.message_count = 0
        self.last_check_time = "从未"
        self.waiting_count = 0
        
        # 检查是否启用RAG智能检索
        self.enable_smart_rag = config.get("knowledge_search", {}).get("enable_smart_rag", False)
        
        if self.enable_smart_rag:
            print("🧠 RAG智能检索已启用")
        else:
            print("🏷️ 使用传统标签检索模式")
    
    def get_knowledge_context(self, content: str, tags: list[str]) -> str:
        """
        获取知识库上下文 - RAG增强版
        
        Args:
            content: 用户的问题内容
            tags: 用户选择的标签
            
        Returns:
            str: 知识库上下文
        """
        # 检查是否跳过知识库
        if "无" in tags:
            log_msg = "📝 已选择'无'背景，跳过知识库检索"
            print(log_msg)
            if self.gui:
                self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
            return ""
        
        # 选择检索模式
        if self.enable_smart_rag:
            return self._smart_rag_retrieval(content, tags)
        else:
            return self._traditional_tag_retrieval(tags)
    
    def _smart_rag_retrieval(self, content: str, tags: list[str]) -> str:
        """
        🧠 智能RAG检索 - 基于问题内容的语义搜索
        """
        try:
            from notion_knowledge_db import NotionKnowledgeDB
            
            # 创建知识库实例
            knowledge_db = NotionKnowledgeDB(self.config)
            
            # 🎯 关键改进：使用用户问题进行智能检索
            log_msg = f"🧠 启动智能RAG检索，问题: {content[:50]}..."
            print(log_msg)
            if self.gui:
                self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
            
            # 使用smart_search_knowledge进行语义搜索
            max_results = self.config.get("knowledge_search", {}).get("max_snippets", 3)
            smart_results = knowledge_db.smart_search_knowledge(content, max_results=max_results)
            
            if not smart_results:
                # 如果智能检索无结果，降级到标签检索
                log_msg = "🔄 智能检索无结果，降级到标签检索"
                print(log_msg)
                if self.gui:
                    self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
                return self._traditional_tag_retrieval(tags)
            
            # 组装智能检索结果
            context_parts = []
            for result in smart_results:
                title = result.get('title', '未知标题')
                snippet = result.get('content', '')
                score = result.get('similarity_score', 0)
                
                context_part = f"""--- 智能检索结果: {title} (相似度: {score:.2f}) ---
{snippet}"""
                context_parts.append(context_part)
                
                log_msg = f"✅ 找到相关知识: {title} (相似度: {score:.2f})"
                print(log_msg)
                if self.gui:
                    self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
            
            final_context = "\n\n".join(context_parts)
            
            # 添加智能检索说明
            rag_header = f"""💡 以下是根据您的问题「{content[:30]}...」智能检索到的相关知识：

{final_context}

📋 检索说明：以上内容通过语义相似度匹配获得，请优先参考高相似度的结果。"""
            
            log_msg = f"🎯 智能RAG检索完成：{len(smart_results)}个结果，{len(rag_header)}字符"
            print(log_msg)
            if self.gui:
                self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
            
            return rag_header
            
        except Exception as e:
            error_msg = f"❌ 智能RAG检索失败: {e}，降级到标签检索"
            print(error_msg)
            if self.gui:
                self.gui.root.after(0, lambda: self.gui.add_log(error_msg))
            return self._traditional_tag_retrieval(tags)
    
    def _traditional_tag_retrieval(self, tags: list[str]) -> str:
        """
        🏷️ 传统标签检索 - 基于标签的文件匹配
        """
        log_msg = f"🏷️ 使用传统标签检索: {tags}"
        print(log_msg)
        if self.gui:
            self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
        
        return self.notion_handler.get_context_from_knowledge_base(tags)
    
    def process_single_message(self, message):
        """处理单条消息 - RAG增强版 + 连续对话支持"""
        try:
            page_id = message["page_id"]
            title = message["title"] or "无标题"
            content = message["content"]
            template_choice = message.get("template_choice", "")
            tags = message.get("tags", [])
            model_choice = message.get("model_choice", "")
            
            process_info = f"正在处理消息:\n模板: {template_choice}\n标签: {tags}\n模型: {model_choice}\n内容: {content[:100]}..."
            print(f"处理消息: {template_choice} - {content[:50]}...")
            
            if self.gui:
                self.gui.root.after(0, lambda: self.gui.add_log(f"开始处理 [{template_choice}]: {content[:30]}..."))
                self.gui.root.after(0, lambda: self.gui.update_current_processing(process_info))
            
            # 🔄 连续对话功能支持
            conversation_context = ""
            session_info = None
            
            if self.conversation_manager.is_enabled():
                # 从消息中提取连续对话字段
                conv_fields = self.notion_handler.extract_conversation_fields_from_message(message)
                
                # 判断是否为连续对话
                if self.conversation_manager.is_conversation_message(conv_fields):
                    # 这是连续对话
                    session_id = conv_fields.get("session_id", "")
                    parent_id = conv_fields.get("parent_id", "")
                    
                    log_msg = f"💬 检测到连续对话，会话ID: {session_id}"
                    print(log_msg)
                    if self.gui:
                        self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
                    
                    # 获取对话历史
                    history = self.conversation_manager.get_conversation_history(session_id, page_id)
                    
                    if history:
                        # 构建对话上下文
                        conversation_context = self.conversation_manager.build_conversation_context(history, content)
                        
                        log_msg = f"📚 加载对话历史：{len(history)}轮，上下文长度：{len(conversation_context)}字符"
                        print(log_msg)
                        if self.gui:
                            self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
                        
                        # 更新会话信息
                        session_info = {
                            "session_id": session_id,
                            "conversation_turn": len(history) + 1,
                            "session_status": "active",
                            "context_length": len(conversation_context)
                        }
                else:
                    # 这是新对话
                    session_info = self.conversation_manager.prepare_new_conversation(page_id)
                    
                    log_msg = f"🆕 创建新对话会话：{session_info['session_id']}"
                    print(log_msg)
                    if self.gui:
                        self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
            else:
                log_msg = "📝 连续对话功能已禁用，使用标准处理模式"
                print(log_msg)
                if self.gui:
                    self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
            
            # 🎯 关键改进：使用增强的知识检索
            knowledge_context = self.get_knowledge_context(content, tags)
            
            # 获取基础系统提示词
            base_system_prompt = self._get_system_prompt(template_choice)
            
            # 🔄 组合系统提示词（支持连续对话 + RAG）
            if knowledge_context and conversation_context:
                # 同时有知识库上下文和对话历史
                if self.enable_smart_rag:
                    system_prompt = f"""{base_system_prompt}

---

## 🧠 智能检索到的相关知识
{knowledge_context}

---

## 💬 对话历史上下文
{conversation_context}

---

## 🎯 执行指令（RAG增强 + 连续对话模式）
请综合利用以上信息回答用户的问题：

1. **对话连续性**：基于对话历史理解上下文，保持回答的连贯性
2. **知识优先级**：优先使用高相似度的智能检索结果
3. **角色保持**：严格遵循角色设定的风格、格式和要求
4. **自然融合**：将知识库内容和对话历史自然地融入回答中
5. **适当引用**：可以提及相关知识来源或引用之前的对话内容
"""
                else:
                    system_prompt = f"""{base_system_prompt}

---

## 📚 补充背景知识
{knowledge_context}

---

## 💬 对话历史上下文
{conversation_context}

---

## 执行指令（连续对话 + 知识增强模式）
请基于对话历史和背景知识，在严格遵循角色设定的前提下回答用户的问题。
"""
            elif knowledge_context:
                # 只有知识库上下文
                if self.enable_smart_rag:
                    system_prompt = f"""{base_system_prompt}

---

## 🧠 智能检索到的相关知识
{knowledge_context}

---

## 🎯 执行指令（RAG增强模式）
请基于以上智能检索到的相关知识来增强您的回答质量：

1. **优先使用高相似度结果**：重点参考相似度较高的知识内容
2. **保持角色设定**：严格遵循上述角色设定的风格、格式和要求
3. **知识融合**：将检索到的知识自然地融入回答中，不要生硬引用
4. **补充说明**：如果检索结果不够充分，请基于您的专业知识进行补充
5. **引用标注**：适当时可以提及相关知识来源以增加可信度
"""
                else:
                    system_prompt = f"""{base_system_prompt}

---

## 补充背景知识
{knowledge_context}

---

## 执行指令
请在严格遵循上述角色设定和输出格式的前提下，充分利用补充背景知识来增强回答质量。
"""
            elif conversation_context:
                # 只有对话历史上下文
                system_prompt = f"""{base_system_prompt}

---

## 💬 对话历史上下文
{conversation_context}

---

## 🎯 执行指令（连续对话模式）
请基于以上对话历史，理解上下文并保持回答的连贯性。请自然地继续这个对话。
"""
            else:
                # 没有额外上下文，使用基础提示词
                system_prompt = base_system_prompt
            
            # 🔄 根据连续对话情况调整用户消息
            if conversation_context:
                # 连续对话模式：直接使用当前问题
                final_content = content
            else:
                # 新对话模式：使用原始内容
                final_content = content

            # 确定要使用的模型ID
            model_mapping = self.config.get("settings", {}).get("model_mapping", {})
            override_model_id = model_mapping.get(model_choice)

            if model_choice and override_model_id:
                log_msg = f"检测到模型选择: {model_choice} -> 使用模型: {override_model_id}"
                print(log_msg)
                if self.gui:
                    self.gui.root.after(0, lambda: self.gui.add_log(log_msg))

            # 检查是否启用自动标题生成
            auto_title = self.config.get("settings", {}).get("auto_generate_title", True)
            title_max_length = self.config.get("settings", {}).get("title_max_length", 20)
            title_min_length = self.config.get("settings", {}).get("title_min_length", 10)
            
            if auto_title:
                # 使用新的处理方法（生成回复+标题）
                success, llm_reply, generated_title = self.llm_handler.process_with_template_and_title(
                    final_content, 
                    system_prompt, 
                    title_max_length, 
                    title_min_length,
                    override_model=override_model_id
                )
            else:
                # 传统处理方法（只生成回复）
                success, llm_reply = self.llm_handler.send_message(
                    final_content, 
                    system_prompt,
                    override_model=override_model_id
                )
                generated_title = None
            
            # 详细日志输出
            print("---------- RAG Enhanced Context Debug ----------")
            print("=== Search Mode ===")
            print(f"RAG Smart Search: {self.enable_smart_rag}")
            print("=== System Prompt ===")
            print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
            print("\n=== Knowledge Context Length ===")
            print(f"Context length: {len(knowledge_context) if knowledge_context else 0} characters")
            print("\n=== LLM Reply ===")
            print(llm_reply[:200] + "..." if len(llm_reply) > 200 else llm_reply)
            print("-----------------------------------------------")

            if success:
                # 成功：更新LLM回复和标题
                update_success = self.notion_handler.update_message_reply(
                    page_id, 
                    llm_reply, 
                    generated_title
                )
                
                if update_success:
                    # 🔄 连续对话：更新会话字段
                    if self.conversation_manager.is_enabled() and session_info:
                        try:
                            # 更新会话相关字段
                            self.conversation_manager.update_session_fields(page_id, session_info)
                            
                            # 记录此次回复到会话历史
                            self.conversation_manager.record_conversation_turn(
                                session_info["session_id"], 
                                page_id, 
                                content, 
                                llm_reply
                            )
                            
                            log_msg = f"💬 会话字段更新成功：{session_info['session_id']} - 第{session_info['conversation_turn']}轮"
                            print(log_msg)
                            if self.gui:
                                self.gui.root.after(0, lambda: self.gui.add_log(log_msg))
                        except Exception as e:
                            error_msg = f"⚠️ 会话字段更新失败: {e}"
                            print(error_msg)
                            if self.gui:
                                self.gui.root.after(0, lambda: self.gui.add_log(error_msg))
                    
                    self.message_count += 1
                    success_msg = f"✅ 消息处理成功 [{template_choice}]: {content[:30]}..."
                    print(success_msg)
                    if self.gui:
                        self.gui.root.after(0, lambda: self.gui.add_log(success_msg))
                else:
                    error_msg = f"❌ 更新Notion失败 [{template_choice}]: {content[:30]}..."
                    print(error_msg)
                    if self.gui:
                        self.gui.root.after(0, lambda: self.gui.add_log(error_msg))
            else:
                # LLM处理失败
                error_msg = f"❌ LLM处理失败 [{template_choice}]: {llm_reply}"
                print(error_msg)
                if self.gui:
                    self.gui.root.after(0, lambda: self.gui.add_log(error_msg))
                    
                # 即使LLM失败，也可以更新一个错误信息到Notion
                error_reply = f"处理失败：{llm_reply}"
                self.notion_handler.update_message_reply(page_id, error_reply, "处理失败")
            
            # 处理间隔（避免API限制）
            time.sleep(2)
            
        except Exception as e:
            error_msg = f"处理消息时出错: {e}"
            print(error_msg)
            
            if self.gui:
                self.gui.root.after(0, lambda: self.gui.add_log(error_msg))
    
    def _get_system_prompt(self, template_choice):
        """根据模板选择获取系统提示词"""
        # 特殊处理：如果选择"无"，则不使用任何提示词模板
        if template_choice == "无":
            return ""
        
        if template_choice:
            template = self.template_manager.get_template(template_choice)
            if template:
                return template["prompt"]
        
        # 回退到默认提示词
        return self.config.get("settings", {}).get("system_prompt", "你是一个智能助手，请认真回答用户的问题。请用中文回复。")


# 💡 使用示例：如何在config.json中启用RAG智能检索
EXAMPLE_CONFIG = {
    "knowledge_search": {
        "enable_smart_rag": True,  # 🎯 关键设置：启用智能RAG检索
        "max_snippets": 3,
        "rag_system": {
            "enabled": True,
            "mode": "hybrid"
        }
    }
} 