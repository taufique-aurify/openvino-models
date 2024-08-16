// Copyright (C) 2019-2020 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#ifndef __COMMAND_LINE_PARSER_H__
#define __COMMAND_LINE_PARSER_H__

#include <algorithm>
#include <cstdarg>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <string.h>
#include <vector>

#define CMD_PARSER_SUCCESS              0
#define CMD_PARSER_ERROR_GENERIC        -1  // general failure
#define CMD_PARSER_ERROR_INVALID_OPTION -2  // user supplied invalid option (options start with '-')
#define CMD_PARSER_ERROR_INVALID_VALUE  -3  // user supplied invalid value for given option type, e.g. "test" for int type option

inline void PrintErrorLogMessage(const char* format, ...)
{
    printf("[Command line parser] [ERROR] ");
    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);

    fflush(stderr);
}

class CommandLineParser
{
public:
    template <typename T> int Add(const char* option_name, const char* option_synonym_name,
        T* output_parameter, const T& default_value, const char* description)
    {
        OptionEntryBase* entry = new OptionEntry<T>(option_name,
            option_synonym_name, output_parameter, default_value, description);
        return Add(option_name, entry);
    }

    int Add(const char* option_name, const char* option_synonym_name,
        std::string* output_parameter, const char* default_value_string, const char* description)
    {
        OptionEntryBase* entry = new OptionEntry<std::string>(option_name,
            option_synonym_name, output_parameter, default_value_string, description);
        return Add(option_name, entry);
    }

    int Parse(int argc, const char* const argv[])
    {
        parsed_options_.clear();
        parsed_positional_.clear();

        int arg = 1;
        for (; arg < argc; arg++)
        {
            // each argv may be option or file/directory
            if (argv[arg][0] == '-')
            {
                std::string option(argv[arg]);
                std::string option_value;

                size_t equal_sign_position = option.find('=');
                bool is_equal_sign = equal_sign_position != std::string::npos;

                // case for format: name=option
                if (is_equal_sign)
                {
                    option_value = option.substr(equal_sign_position + 1);
                    option = option.substr(0, equal_sign_position);
                }
                // else case for option without value, e.g. --version

                int status = ParseOption(option, option_value, is_equal_sign);
                if (status != CMD_PARSER_SUCCESS)
                {
                    return status;
                }
            }
            else
            {
                parsed_positional_.push_back(argv[arg]);
            }
        }

        return CMD_PARSER_SUCCESS;
    }

    void PrintDescription(std::ostream& out = std::cout) const
    {
        out << "Options:\n";

        for (auto const& option : all_options_)
        {
            option.second->PrintDescription(out);
        }

        out.flush();
    }

    size_t GetOptionCount() const
    {
        return parsed_options_.size() / 2; // both option name and synonym are in this container
    }

    bool IsOption(const char* option_name) const
    {
        return std::find(parsed_options_.begin(), parsed_options_.end(),
            std::string(option_name)) != parsed_options_.end();
    }

    size_t GetPositionalCount() const
    {
        return parsed_positional_.size();
    }

    int GetPositional(size_t index, std::string& output_value)
    {
        if (index >= parsed_positional_.size())
        {
            // log message should be printed from app level (app knows what parameter it expects)
            return CMD_PARSER_ERROR_GENERIC;
        }

        output_value = parsed_positional_[index];
        return CMD_PARSER_SUCCESS;
    }

protected:
    class OptionEntryBase
    {
    public:
        OptionEntryBase(const char* option_name, const char* option_synonym_name, const char* description) :
            option_name_(option_name),
            option_synonym_name_(option_synonym_name),
            description_(description) {}

        virtual int SetValue(std::string value) = 0;
        virtual void PrintDescription(std::ostream& out = std::cout) const
        {
            out << " " << std::left << std::setw(10) << option_name_;
            out << ", " << std::setw(20) << option_synonym_name_;
            out << " " << std::setw(10) << TypeName();
            out << " " << description_ << ". ";
        }

        virtual const char* TypeName() const = 0;
        virtual std::string option_name() const { return option_name_; }
        virtual std::string option_synonym_name() const { return option_synonym_name_; }

        virtual bool is_output_parameter() const = 0;

        virtual ~OptionEntryBase() {}
        std::string option_name_;
        std::string option_synonym_name_;
        std::string description_;
    };

private:
    template <typename T> class OptionEntry : public OptionEntryBase
    {
    public:
        OptionEntry(const char* option_name, const char* option_synonym_name,
            T* output_parameter, const T& default_value, const char* description) :
            OptionEntryBase(option_name, option_synonym_name, description),
            output_parameter_(output_parameter),
            default_value_(default_value)
        {
            if (output_parameter_)
            {
                *output_parameter_ = default_value;
            }
        }

        int SetValue(std::string value) override
        {
            if (output_parameter_)
            {
                return ConvertToValue(value.c_str(), *output_parameter_);
            }

            return CMD_PARSER_SUCCESS;
        }

        void PrintDescription(std::ostream& out = std::cout) const override
        {
            OptionEntryBase::PrintDescription(out);
            out << "Default value: " << default_value_;
            out << std::endl;
        }

        bool is_output_parameter() const override { return (output_parameter_ != nullptr); }

    private:
        const char* TypeName() const override
        {
            if (output_parameter_ == nullptr) return "";

            if (typeid(T) == typeid(int)) return "int";
            if (typeid(T) == typeid(float)) return "float";
            if (typeid(T) == typeid(std::string)) return "string";
            if (typeid(T) == typeid(bool)) return "bool";

            return "unknown";
        }

        T* output_parameter_;
        T default_value_;
    };

    int Add(const char* option_name, OptionEntryBase* entry)
    {
        std::unique_ptr<OptionEntryBase> unique_ptr_entry(entry);
        auto result = all_options_.insert(std::make_pair(option_name, std::move(unique_ptr_entry)));
        if (!result.second)
        {
            PrintErrorLogMessage("Failed to add option: %s\n", option_name);
            return CMD_PARSER_ERROR_GENERIC;
        }

        return CMD_PARSER_SUCCESS;
    }

    int ParseOption(std::string name, std::string value, bool is_equal_sign_present)
    {
        for (auto const& option : all_options_)
        {
            if (option.second->option_name() == name ||
                option.second->option_synonym_name() == name)
            {
                // check if it was already parsed
                if (std::find(parsed_options_.begin(), parsed_options_.end(), name) !=
                    parsed_options_.end())
                {
                    PrintErrorLogMessage("Option %s (synonym: %s) is given more than once\n",
                        option.second->option_name().c_str(), option.second->option_synonym_name().c_str());
                    return CMD_PARSER_ERROR_INVALID_OPTION;
                }

                parsed_options_.push_back(option.second->option_name());
                parsed_options_.push_back(option.second->option_synonym_name());

                // if option has output parameter specified but there is no equal sign then return error
                if (!is_equal_sign_present && option.second->is_output_parameter())
                {
                    PrintErrorLogMessage("Syntax error: Option %s requires value\n", name.c_str());
                    return CMD_PARSER_ERROR_INVALID_VALUE;
                }

                int status = CMD_PARSER_SUCCESS;

                // if there is equal sign then:
                //   a. value is not empty
                //   b. value is empty but still we want it to be empty (e.g. -v="" or just -v=)
                if (is_equal_sign_present || !value.empty())
                {
                    status = option.second->SetValue(value);
                }

                return status;
            }
        }

        PrintErrorLogMessage("Invalid option: %s\n", name.c_str());
        return CMD_PARSER_ERROR_INVALID_OPTION;
    }

    template<typename T>
    static int ConvertToValue(const char* string_value, T& converted_value)
    {
        std::istringstream ss(string_value);
        ss >> converted_value;

        if (ss.fail())
        {
            PrintErrorLogMessage("Failed to convert string to value. String: %s\n", string_value);
            return CMD_PARSER_ERROR_INVALID_VALUE;
        }

        return CMD_PARSER_SUCCESS;
    }

    static int ConvertToValue(const char* string_value, std::string& converted_value)
    {
        converted_value = string_value;
        return CMD_PARSER_SUCCESS;
    }

    static int ConvertToValue(const char* string_value, bool& converted_value)
    {
        if (strcmp(string_value, "true") == 0 ||
            strcmp(string_value, "1") == 0 ||
            strcmp(string_value, "yes") == 0)
        {
            converted_value = true;
        }
        else if (strcmp(string_value, "false") == 0 ||
            strcmp(string_value, "0") == 0 ||
            strcmp(string_value, "no") == 0)
        {
            converted_value = false;
        }
        else
        {
            PrintErrorLogMessage("Failed to convert string to bool value. String: %s\n", string_value);
            return CMD_PARSER_ERROR_INVALID_VALUE;
        }

        return CMD_PARSER_SUCCESS;
    }

    std::map<std::string, std::unique_ptr<OptionEntryBase>> all_options_;

    std::vector<std::string> parsed_options_;
    std::vector<std::string> parsed_positional_;
};

template<>
inline void CommandLineParser::OptionEntry<std::string>::PrintDescription(std::ostream& out) const
{
    OptionEntryBase::PrintDescription(out);
    if (!default_value_.empty())
    {
        out << "Default value: " << default_value_;
    }
    out << std::endl;
}


#endif  // __COMMAND_LINE_PARSER_H__
