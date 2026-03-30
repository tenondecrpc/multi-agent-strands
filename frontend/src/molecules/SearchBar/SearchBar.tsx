import { Input } from "@/atoms/Input";
import { Button } from "@/atoms/Button";
import { Icon } from "@/atoms/Icon";
import { cn } from "@/lib/utils";

export interface SearchBarProps {
  value?: string;
  onChange?: (value: string) => void;
  onSubmit?: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export const SearchBar = ({
  value,
  onChange,
  onSubmit,
  placeholder = "Search...",
  className,
}: SearchBarProps) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSubmit && value) {
      onSubmit(value);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={cn("flex w-full max-w-sm items-center space-x-2", className)}
    >
      <Input
        type="text"
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        className="flex-1"
      />
      <Button type="submit" size="icon" variant="ghost">
        <Icon name="search" size="sm" />
      </Button>
    </form>
  );
};
