"""Explicit Pydantic event union in the existing FastAPI OpenAPI pipeline."""

from pydantic import TypeAdapter

from module_admin.entity.vo.text_field_ai_vo import TextFieldAIEvent, TextFieldAIRequest


def install_text_field_ai_openapi(app):
    original = app.openapi

    def openapi():
        schema = original()
        # Isolate event codec definitions from FastAPI's input/output-name mapping.
        events = TypeAdapter(TextFieldAIEvent).json_schema(
            ref_template='#/components/schemas/AIEvent_{model}', mode='serialization'
        )
        definitions = events.pop('$defs', {})
        schema.setdefault('components', {}).setdefault('schemas', {}).update(
            {f'AIEvent_{name}': value for name, value in definitions.items()}
        )
        request = TypeAdapter(TextFieldAIRequest).json_schema(
            ref_template='#/components/schemas/AIRequest_{model}', mode='validation'
        )
        request_definitions = request.pop('$defs', {})
        schema['components']['schemas'].update(
            {f'AIRequest_{name}': value for name, value in request_definitions.items()}
        )
        schema['components']['schemas']['TextFieldAIRequest'] = request
        schema['paths']['/system/ai/text-field/generate']['post']['requestBody'] = {
            'required': True,
            'content': {'application/json': {'schema': {'$ref': '#/components/schemas/TextFieldAIRequest'}}},
        }
        responses = schema['paths']['/system/ai/text-field/generate']['post']['responses']
        responses['200']['content'] = {'text/event-stream': {'schema': events}}
        for status in ('401', '403', '422', '429', '503'):
            responses[status]['content'] = {
                'application/problem+json': {'schema': {'$ref': '#/components/schemas/TextFieldAIProblem'}}
            }
        return schema

    app.openapi = openapi
