import { type ReactNode } from 'react'

/** 轻量 Markdown 渲染器 — 支持流式输出场景 */
export default function Markdown({ text }: { text: string }) {
  const elements = parseMarkdown(text)

  return (
    <div className="prose prose-sm max-w-none break-words
      prose-headings:text-industrial-text prose-headings:font-semibold prose-headings:mb-1 prose-headings:mt-3
      prose-h1:text-lg prose-h2:text-base prose-h3:text-sm prose-h4:text-sm
      prose-p:text-industrial-text prose-p:leading-relaxed prose-p:mb-2
      prose-strong:text-industrial-text prose-strong:font-semibold
      prose-code:bg-industrial-bg prose-code:text-industrial-accent prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-mono prose-code:before:hidden prose-code:after:hidden
      prose-pre:bg-industrial-bg prose-pre:border prose-pre:border-industrial-border prose-pre:rounded-lg prose-pre:p-3 prose-pre:overflow-auto prose-pre:text-xs
      prose-pre:code:bg-transparent prose-pre:code:p-0 prose-pre:code:border-0
      prose-ul:list-disc prose-ol:list-decimal prose-li:text-industrial-text-secondary prose-li:mb-1
      prose-ul:pl-5 prose-ol:pl-5 prose-li:pl-0.5
      prose-a:text-industrial-primary prose-a:underline
    ">
      {elements.map((el, i) => (
        <span key={i}>{el}</span>
      ))}
    </div>
  )
}

type MdNode = { type: string; content: string; children?: MdNode[] }

function parseMarkdown(text: string): ReactNode[] {
  if (!text) return [null]
  
  const lines = text.split('\n')
  const elements: ReactNode[] = []
  let i = 0
  
  while (i < lines.length) {
    const line = lines[i]

    // 代码块 ``` ... ```
    if (line.trimStart().startsWith('```')) {
      const lang = line.trimStart().slice(3).trim()
      const codeLines: string[] = []
      i++
      while (i < lines.length && !lines[i].trimStart().startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      i++ // skip closing ```
      elements.push(
        <pre key={elements.length} className="my-2">
          <code>{codeLines.join('\n') || '\n'}</code>
        </pre>
      )
      continue
    }

    // 空行
    if (line.trim() === '') {
      i++
      continue
    }

    // 标题 # ## ###
    const headingMatch = line.match(/^(#{1,4})\s+(.+)$/)
    if (headingMatch) {
      const level = headingMatch[1].length
      const content = renderInline(headingMatch[2])
      const Tag = `h${level}` as keyof JSX.IntrinsicElements
      elements.push(<Tag key={elements.length}>{content}</Tag>)
      i++
      continue
    }

    // 无序列表 - item
    if (/^[\s]*[-*+]\s+/.test(line)) {
      const items: ReactNode[] = []
      while (i < lines.length && /^[\s]*[-*+]\s+/.test(lines[i])) {
        const content = renderInline(lines[i].replace(/^[\s]*[-*+]\s+/, ''))
        items.push(<li key={items.length}>{content}</li>)
        i++
      }
      elements.push(<ul key={elements.length}>{items}</ul>)
      continue
    }

    // 有序列表 1. item
    if (/^[\s]*\d+\.\s+/.test(line)) {
      const items: ReactNode[] = []
      while (i < lines.length && /^[\s]*\d+\.\s+/.test(lines[i])) {
        const content = renderInline(lines[i].replace(/^[\s]*\d+\.\s+/, ''))
        items.push(<li key={items.length}>{content}</li>)
        i++
      }
      elements.push(<ol key={elements.length}>{items}</ol>)
      continue
    }

    // 普通段落
    const content = renderInline(line)
    elements.push(<p key={elements.length}>{content}</p>)
    i++
  }
  
  return elements
}

function renderInline(text: string): ReactNode[] {
  if (!text) return [null]
  
  const parts: ReactNode[] = []
  // 分割 inline code `...`
  const segs = text.split(/(`[^`]+`)/)
  
  segs.forEach((seg, idx) => {
    if (seg.startsWith('`') && seg.endsWith('`')) {
      parts.push(<code key={idx}>{seg.slice(1, -1)}</code>)
      return
    }
    // 处理 **bold** 和 *italic*
    parts.push(...renderBoldItalic(seg, idx * 1000))
  })
  
  return parts
}

function renderBoldItalic(text: string, baseKey: number): ReactNode[] {
  const parts: ReactNode[] = []
  // Bold **...**
  const boldSegs = text.split(/(\*\*[^*]+\*\*)/)
  boldSegs.forEach((seg) => {
    if (seg.startsWith('**') && seg.endsWith('**')) {
      parts.push(<strong key={baseKey++}>{seg.slice(2, -2)}</strong>)
    } else {
      // Italic *...* (but not **)
      const italicSegs = seg.split(/(\*[^*]+\*)/)
      italicSegs.forEach((is) => {
        if (is.startsWith('*') && is.endsWith('*')) {
          parts.push(<em key={baseKey++}>{is.slice(1, -1)}</em>)
        } else if (is) {
          parts.push(<span key={baseKey++}>{is}</span>)
        }
      })
    }
  })
  return parts
}
