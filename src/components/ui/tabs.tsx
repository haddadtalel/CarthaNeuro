"use client"

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const tabsListVariants = cva(
  "inline-flex items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground",
  {
    variants: {
      orientation: {
        horizontal: "h-10 flex-row",
        vertical: "h-full w-10 flex-col",
      },
    },
    defaultVariants: {
      orientation: "horizontal",
    },
  }
)

const tabsTriggerVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm",
  {
    variants: {
      variant: {
        default: "data-[state=active]:bg-background data-[state=active]:text-foreground",
        outline:
          "data-[state=active]:bg-background data-[state=active]:text-foreground border border-input",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const tabsContentVariants = cva(
  "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
  {
    variants: {
      orientation: {
        horizontal: "",
        vertical: "ml-2",
      },
    },
    defaultVariants: {
      orientation: "horizontal",
    },
  }
)

export interface TabsProps
  extends React.HTMLAttributes<HTMLDivElement> {
  value?: string
  defaultValue?: string
  onValueChange?: (value: string) => void
  orientation?: "horizontal" | "vertical"
}

export interface TabsListProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof tabsListVariants> {}

export interface TabsTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof tabsTriggerVariants> {
  value: string
}

export interface TabsContentProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof tabsContentVariants> {
  value: string
}

const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  ({ className, value, defaultValue, onValueChange, orientation = "horizontal", ...props }, ref) => {
    const [internalValue, setInternalValue] = React.useState(defaultValue || "")
    const isControlled = value !== undefined

    const currentValue = isControlled ? value : internalValue

    const handleValueChange = (newValue: string) => {
      if (!isControlled) {
        setInternalValue(newValue)
      }
      onValueChange?.(newValue)
    }

    return (
      <div
        ref={ref}
        data-orientation={orientation}
        className={className}
        {...props}
      >
        <TabsContext.Provider
          value={{
            value: currentValue,
            onValueChange: handleValueChange,
            orientation,
          }}
        >
          {props.children}
        </TabsContext.Provider>
      </div>
    )
  }
)
Tabs.displayName = "Tabs"

const TabsContext = React.createContext<{
  value?: string
  onValueChange?: (value: string) => void
  orientation?: "horizontal" | "vertical"
}>({})

const TabsList = React.forwardRef<HTMLDivElement, TabsListProps>(
  ({ className, orientation, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(tabsListVariants({ orientation }), className)}
      {...props}
    />
  )
)
TabsList.displayName = "TabsList"

const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ className, variant, value, ...props }, ref) => {
    const context = React.useContext(TabsContext)
    const isActive = context.value === value

    return (
      <button
        ref={ref}
        className={cn(tabsTriggerVariants({ variant }), className)}
        data-state={isActive ? "active" : "inactive"}
        onClick={() => context.onValueChange?.(value)}
        {...props}
      />
    )
  }
)
TabsTrigger.displayName = "TabsTrigger"

const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
  ({ className, value, orientation, ...props }, ref) => {
    const context = React.useContext(TabsContext)
    const isActive = context.value === value

    if (!isActive) return null

    return (
      <div
        ref={ref}
        className={cn(tabsContentVariants({ orientation }), className)}
        data-state={isActive ? "active" : "inactive"}
        {...props}
      />
    )
  }
)
TabsContent.displayName = "TabsContent"

export { Tabs, TabsList, TabsTrigger, TabsContent }