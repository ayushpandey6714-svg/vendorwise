"""Run inside a started sample-demo container; makes no external AI calls."""
from pathlib import Path
import httpx


def main():
    root = Path(__file__).resolve().parents[1]
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=60) as client:
        def call(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        health = call('GET', '/health').json()
        assert health['mode'] == 'fixture' and health['public_demo']
        analysis = call('POST', '/analyses', json=dict(quantity=20, budget='1200000',
            min_ram_gb=16, min_storage_gb=512, min_warranty_months=36, max_delivery_days=10)).json()
        aid = analysis['analysis_id']
        call('POST', f'/analyses/{aid}/documents', files=[('files',
            (f'vendor_{v}.pdf', (root/f'samples/vendor_{v}.pdf').read_bytes(), 'application/pdf'))
            for v in ('a','b','c')])
        quotes = call('POST', f'/analyses/{aid}/extract').json()
        names = {q['document_id']:q['vendor']['value'] for q in quotes}
        result = call('POST', f'/analyses/{aid}/compare').json()
        assert [names[i] for i in result['recommendation_ids']] == ['Vendor C']
        changed = call('POST', f'/analyses/{aid}/what-if', json=dict(budget='1200000',
            min_warranty_months=36, max_delivery_days=14)).json()
        assert [names[i] for i in changed['updated']['recommendation_ids']] == ['Vendor B']
        assert float(changed['savings']) == 30000
        answer = call('POST', f'/analyses/{aid}/ask', json={'question':'Does Vendor B cover the battery?'}).json()
        assert answer['mode'] == 'fixture' and answer['citations']
        assert 'Vendor B' in call('GET', f'/analyses/{aid}/report').text
        print('Container sample workflow passed: extraction, comparison, what-if, cited fixture Q&A, report.')


if __name__ == '__main__':
    main()
