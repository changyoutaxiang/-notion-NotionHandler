# Notion知识库数据库设计

## 🗄️ 主知识库数据库 (Knowledge Database)

### 数据库属性配置

| 字段名称 | 字段类型 | 必需 | 说明 | 配置选项 |
|---------|---------|------|------|----------|
| **知识标题** | Title | ✅ | 知识条目的标题 | 作为数据库Title字段 |
| **知识分类** | Select | ✅ | 一级分类 | 选项：业务知识、技术文档、流程规范、部门介绍 |
| **知识子类** | Select | ⚪ | 二级分类 | 根据一级分类动态调整 |
| **关键词** | Multi-select | ✅ | 检索关键词标签 | 预设常用关键词 |
| **适用场景** | Multi-select | ⚪ | 适用的问题类型 | 预设场景类型 |
| **优先级** | Select | ✅ | 检索排序权重 | 高、中、低 |
| **状态** | Select | ✅ | 知识状态 | 启用、禁用、待审核 |
| **关联知识** | Relation | ⚪ | 关联到其他知识条目 | 关联到本数据库 |
| **使用频率** | Number | ⚪ | 系统自动统计调用次数 | 默认值：0 |
| **创建人** | People | ⚪ | 知识创建者 | 自动记录 |
| **最后更新** | Last edited time | ⚪ | 最后编辑时间 | 自动记录 |

### 详细字段配置

#### 知识分类选项
```
业务知识
├── 部门介绍
├── 业务流程  
├── 产品介绍
└── 服务说明

技术文档
├── 技术规范
├── 操作指南
├── 系统说明
└── 故障处理

流程规范
├── 工作流程
├── 审批流程
├── 操作规范
└── 质量标准

部门介绍
├── 组织架构
├── 职能说明
├── 联系方式
└── 团队介绍
```

#### 预设关键词标签
```
核心业务: AI效率中心、业务理解、部门职能、组织架构
技术相关: 系统操作、技术支持、故障处理、使用指南
流程相关: 工作流程、审批流程、操作规范、质量管理
通用标签: 介绍、说明、指南、帮助、FAQ
```

#### 适用场景选项
```
用户咨询: 部门介绍、职能咨询、业务了解、联系方式
技术支持: 操作指导、故障解决、系统使用、功能说明
流程指导: 审批流程、工作流程、规范要求、质量标准
一般查询: 常见问题、基础信息、背景资料、参考文档
```

## 🏷️ 分类词典数据库 (Category Dictionary)

### 数据库属性配置

| 字段名称 | 字段类型 | 说明 | 配置选项 |
|---------|---------|------|----------|
| **分类名称** | Title | 分类的名称 | 作为数据库Title字段 |
| **分类类型** | Select | 一级分类、二级分类 | 一级分类、二级分类 |
| **父分类** | Relation | 关联到上级分类 | 关联到本数据库 |
| **描述** | Text | 分类的用途说明 | 多行文本 |
| **状态** | Select | 启用、禁用 | 启用、禁用 |
| **排序** | Number | 显示顺序 | 数字，默认100 |

## 📋 页面内容模板

### 知识条目页面结构
```markdown
# 知识摘要
[50-100字的核心摘要，用于快速匹配和预览]

## 详细内容
[完整的知识内容，支持富文本格式]

## 适用场景说明
- 📋 场景1：用户询问部门职能时
- 🔍 场景2：需要了解组织架构时  
- 💼 场景3：业务合作咨询时

## 相关知识参考
- 🔗 参考：[其他相关知识条目]
- 📚 延伸：[深度阅读建议]

## 使用统计
- 📊 调用次数：{自动更新}
- 📅 最近使用：{自动更新}

## 更新记录
- 2025-01-20：创建初版
- 2025-01-25：补充使用场景
```

## 🔧 配置文件扩展

### config.json 新增配置段
```json
{
  "notion": {
    // 现有配置保持不变...
    
    // 新增知识库配置
    "knowledge_database_id": "填入知识库数据库ID",
    "category_database_id": "填入分类词典数据库ID",
    
    // 知识库字段名配置
    "knowledge_title_property": "知识标题",
    "knowledge_category_property": "知识分类", 
    "knowledge_subcategory_property": "知识子类",
    "knowledge_keywords_property": "关键词",
    "knowledge_scenarios_property": "适用场景",
    "knowledge_priority_property": "优先级",
    "knowledge_status_property": "状态",
    "knowledge_relations_property": "关联知识",
    "knowledge_usage_property": "使用频率"
  },
  
  "knowledge_search": {
    "max_context_length": 4000,
    "max_snippets": 5,
    "similarity_threshold": 0.3,
    "enable_semantic_search": true,
    "enable_usage_weighting": true,
    "snippet_max_length": 800,
    "enable_new_system": false
  }
}
```

## 📦 创建步骤

### 第一步：创建主知识库数据库
1. 在Notion中新建数据库 "知识库管理"
2. 按照上述表格配置所有属性字段
3. 设置合适的视图和筛选器
4. 复制数据库ID到配置文件

### 第二步：创建分类词典数据库
1. 在Notion中新建数据库 "知识分类词典"
2. 按照表格配置属性字段
3. 录入预设的分类数据
4. 复制数据库ID到配置文件

### 第三步：迁移现有知识
1. 将 AI效率中心.md 转换为第一个知识条目
2. 将 业务理解.md 转换为第二个知识条目
3. 为每个知识条目设置适当的分类和关键词

---

*设计文档版本: v1.0*  
*创建时间: 2025-01-20* 